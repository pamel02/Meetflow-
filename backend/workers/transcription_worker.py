"""
workers/transcription_worker.py
════════════════════════════════════════════════════════════════════════════════
Deux workers distincts :

1. transcribe_segment_now(segment_id, app)
   ─ Déclenché immédiatement à chaque upload de segment (60s).
   ─ Transcrit avec Whisper, stocke le texte dans AudioSegment.transcript_text.
   ─ Tourne dans son propre thread daemon.
   ─ La réunion peut continuer à enregistrer en parallèle.

2. start_summary_pipeline(meeting_id, app)
   ─ Déclenché par end_meeting().
   ─ Attend que TOUS les segments soient transcrits (poll interne).
   ─ Fusionne les textes (déduplication du chevauchement 5s).
   ─ Génère titre + bilan JSON complet (LLM).
   ─ Indexe dans ChromaDB.
   ─ Génère le PDF.

Économie de tokens :
   ─ Le LLM ne reçoit que du texte brut (pas de balises HTML/MD).
   ─ Les prompts sont en .md minimalistes.
   ─ Le bilan final est un seul appel JSON (pas de map-reduce sauf longues réunions).
════════════════════════════════════════════════════════════════════════════════
"""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Verrou global : Whisper est lourd, on ne lance qu'une transcription à la fois
_whisper_lock = threading.Lock()

# Bound background work so repeated uploads cannot create unbounded threads.
_executor = ThreadPoolExecutor(
    max_workers=int(os.environ.get("WORKER_MAX_THREADS", "4")),
    thread_name_prefix="meeting-worker",
)


def submit_background(function, *args):
    """Submit bounded in-process work through the shared executor."""
    return _executor.submit(function, *args)

# Délai de polling (secondes) pour attendre les transcriptions en cours
_POLL_INTERVAL = 5
# Timeout maximum d'attente après end_meeting (secondes) : 20 min
_WAIT_TIMEOUT  = 1200


# ══════════════════════════════════════════════════════════════════════════════
# 1. WORKER TEMPS RÉEL — un segment = un thread
# ══════════════════════════════════════════════════════════════════════════════

def transcribe_segment_now(segment_id: int, app) -> None:
    """
    Lance la transcription d'un segment dans un thread daemon.
    Appelé dès que audio_service reçoit un fichier.
    """
    submit_background(_run_transcribe_segment, segment_id, app)
    logger.debug(f"Thread de transcription lancé pour segment {segment_id}.")


def _run_transcribe_segment(segment_id: int, app) -> None:
    with app.app_context():
        _transcribe_segment(segment_id)


def _transcribe_segment(segment_id: int) -> None:
    """
    Transcrit un segment audio avec Whisper et stocke le résultat.
    Utilise un verrou global pour éviter de saturer la RAM avec plusieurs
    instances Whisper simultanées.
    """
    from ai.whisper_model import transcribe_file
    from models.AudioSegment import AudioSegment, SegmentStatus
    from repositories.audio_repository import AudioRepository

    # Récupère le segment
    seg = AudioSegment.query.get(segment_id)
    if not seg:
        logger.error(f"Segment {segment_id} introuvable.")
        return

    if seg.status == SegmentStatus.TRANSCRIBED:
        logger.debug(f"Segment {segment_id} déjà transcrit. Ignoré.")
        return

    logger.info(f"[Meeting {seg.meeting_id}] Transcription segment {seg.segment_number}…")
    AudioRepository.mark_processing(seg)

    try:
        # Verrou : une seule transcription Whisper à la fois (économie RAM)
        with _whisper_lock:
            result = transcribe_file(seg.filename)

        text     = result.get("text", "").strip()
        language = result.get("language")

        AudioRepository.mark_transcribed(seg, text=text, language=language)
        logger.info(
            f"[Meeting {seg.meeting_id}] Segment {seg.segment_number} transcrit "
            f"({len(text)} chars, langue={language})."
        )

    except Exception as e:
        logger.error(
            f"[Meeting {seg.meeting_id}] Erreur transcription segment "
            f"{seg.segment_number} : {e}", exc_info=True
        )
        AudioRepository.mark_error(seg, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 2. WORKER FIN DE RÉUNION — bilan complet
# ══════════════════════════════════════════════════════════════════════════════

def start_summary_pipeline(meeting_id: int, app) -> None:
    """
    Lance le pipeline de bilan dans un thread daemon.
    Appelé par audio_service.end_meeting().
    """
    submit_background(_run_summary_pipeline, meeting_id, app)
    logger.info(f"Pipeline de bilan lancé pour réunion {meeting_id}.")


def _run_summary_pipeline(meeting_id: int, app) -> None:
    with app.app_context():
        _summary_pipeline(meeting_id)


def _summary_pipeline(meeting_id: int) -> None:
    """
    Pipeline de fin de réunion :

    1. Attente que tous les segments soient transcrits.
    2. Fusion des textes (déduplication chevauchement 5s).
    3. Sauvegarde de la transcription complète.
    4. Génération titre automatique (si absent).
    5. Génération du bilan JSON complet via LLM.
    6. Persistance en base (summary, decisions, actions, questions, risks).
    7. Indexation ChromaDB (RAG).
    8. Génération PDF.
    9. Statut COMPLETED.
    """
    import os

    from flask import current_app

    from ai.chunker import merge_segment_transcripts
    from ai.rag import RAGService
    from ai.summarizer import generate_full_report, generate_title
    from models.Meeting import MeetingStatus
    from repositories.audio_repository import AudioRepository
    from repositories.meeting_repository import MeetingRepository
    from repositories.summary_repository import SummaryRepository
    from utils.pdf import generate_meeting_pdf

    meeting = MeetingRepository.find_by_id(meeting_id)
    if not meeting:
        logger.error(f"Réunion {meeting_id} introuvable. Pipeline bilan annulé.")
        return

    def _status(step: str, progress: int, status: str = MeetingStatus.TRANSCRIBING):
        MeetingRepository.update_status(meeting, status, step=step, progress=progress)
        logger.info(f"[Meeting {meeting_id}] [{progress}%] {step}")

    try:
        # ── 1. Attente que tous les segments soient transcrits ────────────
        _status("En attente de la fin des transcriptions…", 5)

        elapsed = 0
        while elapsed < _WAIT_TIMEOUT:
            if AudioRepository.all_transcribed(meeting_id):
                break
            pending = AudioRepository.find_untranscribed(meeting_id)
            logger.info(
                f"[Meeting {meeting_id}] Attente : {len(pending)} segment(s) "
                f"encore en cours de transcription…"
            )
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
        else:
            # Timeout : on tente quand même avec ce qui est disponible
            logger.warning(
                f"[Meeting {meeting_id}] Timeout d'attente ({_WAIT_TIMEOUT}s). "
                f"Bilan sur les segments transcrits disponibles."
            )

        # ── 2. Récupère les textes transcrits dans l'ordre ────────────────
        _status("Fusion des transcriptions", 20)

        transcribed_segs = AudioRepository.find_transcribed(meeting_id)

        if transcribed_segs:
            texts = [s.transcript_text for s in transcribed_segs if s.transcript_text]
            if not texts:
                raise RuntimeError("Les segments transcrits ne contiennent pas de texte.")

            # ── 3. Fusion (déduplication du chevauchement 5s) ─────────────
            full_transcript = merge_segment_transcripts(texts)

            # Durée totale
            total_duration = sum(s.duration or 0 for s in transcribed_segs)
            MeetingRepository.update(meeting, duration=int(total_duration))

            # Langue majoritaire détectée
            languages = [s.detected_language for s in transcribed_segs if s.detected_language]
            dominant_lang = max(set(languages), key=languages.count) if languages else "fr"

            SummaryRepository.save_transcript(
                meeting_id, full_transcript, language=dominant_lang
            )
            logger.info(
                f"[Meeting {meeting_id}] Transcription complète : "
                f"{len(full_transcript)} chars, {len(transcribed_segs)} segments, "
                f"langue={dominant_lang}."
            )
        else:
            # Une réunion importée ou de démonstration peut déjà posséder une
            # transcription complète sans AudioSegment associé.
            existing_transcript = SummaryRepository.get_transcript(meeting_id)
            full_transcript = (
                existing_transcript.full_text.strip()
                if existing_transcript and existing_transcript.full_text
                else ""
            )
            if not full_transcript:
                raise RuntimeError("Aucune transcription disponible pour le bilan.")
            dominant_lang = existing_transcript.language or "fr"
            logger.info(
                f"[Meeting {meeting_id}] Utilisation de la transcription complète "
                f"existante ({len(full_transcript)} chars, langue={dominant_lang})."
            )

        # ── 4. Titre automatique ──────────────────────────────────────────
        _status("Génération du titre", 35, MeetingStatus.ANALYZING)

        if not meeting.title:
            title = generate_title(full_transcript)
            MeetingRepository.update(meeting, title=title)
            logger.info(f"[Meeting {meeting_id}] Titre généré : «{title}»")

        # ── 5. Bilan JSON complet (un seul appel LLM) ─────────────────────
        _status("Génération du bilan IA", 50, MeetingStatus.ANALYZING)

        report = generate_full_report(full_transcript)
        # report = {
        #   "general_summary": str,
        #   "participants":    [str],
        #   "conclusion":      str,
        #   "decisions":       [{content, context}],
        #   "actions":         [{content, responsible, deadline}],
        #   "questions":       [{content, context}],
        #   "risks":           [{content, severity, mitigation}]
        # }

        # ── 6. Persistance en base ────────────────────────────────────────
        _status("Enregistrement du bilan", 70, MeetingStatus.ANALYZING)

        SummaryRepository.save_summary(
            meeting_id=meeting_id,
            general_summary=report.get("general_summary", ""),
            participants=report.get("participants", []),
            conclusion=report.get("conclusion", "")
        )
        SummaryRepository.save_decisions(meeting_id, report.get("decisions", []))
        SummaryRepository.save_actions(meeting_id,   report.get("actions", []))
        SummaryRepository.save_questions(meeting_id, report.get("questions", []))
        SummaryRepository.save_risks(meeting_id,     report.get("risks", []))

        logger.info(
            f"[Meeting {meeting_id}] Bilan persisté : "
            f"{len(report.get('decisions',[]))} décisions, "
            f"{len(report.get('actions',[]))} actions, "
            f"{len(report.get('questions',[]))} questions, "
            f"{len(report.get('risks',[]))} risques."
        )

        # ── 7. Indexation ChromaDB ────────────────────────────────────────
        _status("Indexation RAG", 82, MeetingStatus.ANALYZING)

        try:
            nb = RAGService.index_meeting(
                meeting_id=meeting_id,
                transcript_text=full_transcript,
                meeting_title=meeting.title
            )
            logger.info(f"[Meeting {meeting_id}] RAG : {nb} chunks indexés.")
        except Exception as e:
            logger.error(f"[Meeting {meeting_id}] Erreur RAG (non bloquant) : {e}")

        # ── 8. Génération PDF ─────────────────────────────────────────────
        _status("Génération du PDF", 92, MeetingStatus.ANALYZING)

        try:
            export_dir  = current_app.config.get("EXPORT_FOLDER", "./exports")
            os.makedirs(export_dir, exist_ok=True)
            pdf_path    = os.path.join(export_dir, f"meeting_{meeting_id}_report.pdf")

            summary_obj    = SummaryRepository.get_summary(meeting_id)
            decisions      = SummaryRepository.get_decisions(meeting_id)
            actions        = SummaryRepository.get_actions(meeting_id)
            questions      = SummaryRepository.get_questions(meeting_id)
            risks          = SummaryRepository.get_risks(meeting_id)

            generate_meeting_pdf(
                output_path=pdf_path,
                meeting=meeting,
                summary=summary_obj,
                # Le compte rendu principal reste synthétique. La transcription
                # demeure disponible dans l'application et via l'export explicite.
                transcript=None,
                decisions=decisions,
                actions=actions,
                questions=questions,
                risks=risks
            )
            SummaryRepository.set_pdf_path(meeting_id, pdf_path)
            logger.info(f"[Meeting {meeting_id}] PDF : {pdf_path}")
        except Exception as e:
            logger.error(f"[Meeting {meeting_id}] Erreur PDF (non bloquant) : {e}")

        # ── 9. Terminé ────────────────────────────────────────────────────
        _status("Traitement terminé", 100, MeetingStatus.COMPLETED)
        logger.info(f"[Meeting {meeting_id}] Pipeline bilan terminé avec succès.")

    except Exception as e:
        logger.error(
            f"[Meeting {meeting_id}] Erreur critique pipeline bilan : {e}",
            exc_info=True
        )
        from models.Meeting import MeetingStatus as MS
        MeetingRepository.update(
            meeting,
            status=MS.ERROR,
            error_message=str(e),
            processing_step="Erreur",
            processing_progress=0
        )
