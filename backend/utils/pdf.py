"""
utils/pdf.py - Génération du PDF du compte rendu avec ReportLab
Structure : en-tête → participants → résumé → décisions → actions → questions → risques → conclusion → transcription

Design :
- Aucun tableau (Table) n'est utilisé nulle part dans ce document. Chaque
  élément (action, décision, question, risque...) est construit comme un
  bloc de paragraphes empilés (Paragraph + Spacer + filet séparateur), ce
  qui permet au texte de s'étendre sur autant de lignes que nécessaire sans
  jamais déborder d'une cellule, quelle que soit sa longueur.
- Palette "sobre et riche" : bordeaux, brun, taupe foncé. Pas de bleu, pas
  d'or/jaune, pas de couleurs vives. Pas d'émojis.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_meeting_pdf(output_path: str, meeting, summary,
                          transcript=None, decisions=None,
                          actions=None, questions=None, risks=None) -> str:
    """
    Génère un PDF complet du compte rendu d'une réunion.

    Args:
        output_path : Chemin de sortie du fichier PDF.
        meeting     : Objet Meeting SQLAlchemy.
        summary     : Objet Summary SQLAlchemy.
        transcript  : Objet Transcript (optionnel).
        decisions   : Liste d'objets Decision.
        actions     : Liste d'objets Action.
        questions   : Liste d'objets Question.
        risks       : Liste d'objets Risk.

    Returns:
        Chemin du fichier PDF généré.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except ImportError:
        logger.error("reportlab non installé. pip install reportlab")
        raise

    # ── Palette de couleurs (bordeaux / brun, sans bleu ni or) ─────────────
    C_BORDEAUX      = colors.HexColor("#5B1A22")   # titre principal
    C_BORDEAUX_SOFT = colors.HexColor("#7A2E35")   # accents / filets
    C_BRUN          = colors.HexColor("#4A3628")   # titres de section (H1)
    C_BRUN_CLAIR    = colors.HexColor("#6B5442")   # sous-titres (H2)
    C_TAUPE         = colors.HexColor("#8C7B6B")   # texte secondaire / métadonnées
    C_TEXTE         = colors.HexColor("#2B2420")   # corps de texte
    C_FILET_CLAIR   = colors.HexColor("#D9CFC2")   # filets discrets
    colors.HexColor("#FAF7F2")   # fond très léger pour respirer
    C_SEV_HAUT      = colors.HexColor("#7A2E35")   # risque élevé (bordeaux)
    C_SEV_MOYEN     = colors.HexColor("#8C6A4A")   # risque moyen (brun doux)
    C_SEV_FAIBLE    = colors.HexColor("#5E6E58")   # risque faible (vert olive discret)

    # ── Styles ────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "ReunionTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=25,
        spaceAfter=4,
        textColor=C_BORDEAUX,
        alignment=0,
    )
    style_subtitle = ParagraphStyle(
        "ReunionSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10.5,
        textColor=C_TAUPE,
        spaceAfter=2,
    )
    style_h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13.5,
        spaceBefore=20,
        spaceAfter=8,
        textColor=C_BRUN,
        borderWidth=0,
    )
    ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        spaceBefore=8,
        spaceAfter=3,
        textColor=C_BRUN_CLAIR,
    )
    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=C_TEXTE,
        spaceAfter=4,
    )
    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=C_TAUPE,
        leading=12,
        spaceAfter=2,
    )
    ParagraphStyle(
        "MetaBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_BRUN,
        leading=12,
    )
    style_item_title = ParagraphStyle(
        "ItemTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=C_TEXTE,
        spaceAfter=2,
    )
    style_item_body = ParagraphStyle(
        "ItemBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=C_TEXTE,
        spaceAfter=2,
    )
    style_item_note = ParagraphStyle(
        "ItemNote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=C_TAUPE,
        spaceAfter=2,
    )
    style_footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=C_TAUPE,
    )
    style_transcript = ParagraphStyle(
        "Transcript",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=C_TEXTE,
        spaceAfter=6,
    )

    # ── Petits utilitaires de mise en page ──────────────────────────────
    def thin_rule(color=C_FILET_CLAIR, thickness=0.6):
        return HRFlowable(width="100%", thickness=thickness, color=color,
                           spaceBefore=4, spaceAfter=8)

    def escape(text):
        """Échappe le texte pour l'utiliser dans un Paragraph (balises XML de reportlab)."""
        if text is None:
            return ""
        text = str(text)
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))

    def section_header(text, count=None):
        label = escape(text)
        if count is not None:
            label += f' <font color="#{C_TAUPE.hexval()[2:]}" size="9">({count})</font>'
        block = [Paragraph(label, style_h1)]
        block.append(HRFlowable(width="100%", thickness=1.1, color=C_BORDEAUX_SOFT,
                                 spaceBefore=0, spaceAfter=10))
        return block

    # ── Document ─────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.2*cm,
        leftMargin=2.2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=meeting.title or "Compte rendu de réunion",
        author="Assistant IA de Réunion"
    )

    story = []

    # ── En-tête ──────────────────────────────────────────────────────────
    story.append(Paragraph(escape(meeting.title or "Compte rendu de réunion"), style_title))
    story.append(HRFlowable(width="100%", thickness=1.6, color=C_BORDEAUX))
    story.append(Spacer(1, 0.35*cm))

    created = meeting.created_at.strftime("%d/%m/%Y à %H:%M") if meeting.created_at else "—"
    try:
        from utils.audio import format_duration
        duration_str = format_duration(meeting.duration or 0)
    except Exception:
        duration_str = str(meeting.duration or "—")

    meta_lines = [f"Date : {escape(created)}", f"Durée : {escape(duration_str)}",
                  f"Statut : {escape(meeting.status)}"]
    story.append(Paragraph("  |  ".join(meta_lines), style_subtitle))
    if getattr(meeting, "description", None):
        story.append(Spacer(1, 0.15*cm))
        story.append(Paragraph(escape(meeting.description), style_meta))
    story.append(Spacer(1, 0.4*cm))

    # ── Participants ─────────────────────────────────────────────────────
    if summary and getattr(summary, "participants", None):
        import json
        try:
            participants = (json.loads(summary.participants)
                             if isinstance(summary.participants, str)
                             else summary.participants)
        except Exception:
            participants = []

        if participants:
            story += section_header("Participants")
            story.append(Paragraph(escape(", ".join(participants)), style_body))

    # ── Résumé général ───────────────────────────────────────────────────
    if summary and getattr(summary, "general_summary", None):
        story += section_header("Résumé général")
        story.append(Paragraph(escape(summary.general_summary), style_body))

    # ── Décisions ────────────────────────────────────────────────────────
    if decisions:
        story += section_header("Décisions prises", count=len(decisions))
        for i, d in enumerate(decisions, 1):
            block = [Paragraph(f"{i}. {escape(d.content)}", style_item_title)]
            if getattr(d, "context", None):
                block.append(Paragraph(f"Contexte : {escape(d.context)}", style_item_note))
            block.append(Spacer(1, 0.15*cm))
            story.append(KeepTogether(block))
        story.append(thin_rule())

    # ── Actions à réaliser (sans tableau) ───────────────────────────────
    if actions:
        story += section_header("Actions à réaliser", count=len(actions))
        for i, a in enumerate(actions, 1):
            block = [Paragraph(f"{i}. {escape(a.content)}", style_item_title)]

            details = []
            if getattr(a, "responsible", None):
                details.append(f"Responsable : {escape(a.responsible)}")
            if getattr(a, "deadline", None):
                details.append(f"Échéance : {escape(a.deadline)}")
            if details:
                block.append(Paragraph("   —   ".join(details), style_meta))

            block.append(Spacer(1, 0.1*cm))
            block.append(HRFlowable(width="100%", thickness=0.5, color=C_FILET_CLAIR,
                                     spaceBefore=2, spaceAfter=10))
            story.append(KeepTogether(block))

    # ── Questions ouvertes ───────────────────────────────────────────────
    if questions:
        story += section_header("Questions ouvertes", count=len(questions))
        for i, q in enumerate(questions, 1):
            block = [
                Paragraph(f"{i}. {escape(q.content)}", style_item_body),
                Spacer(1, 0.15*cm),
            ]
            story.append(KeepTogether(block))
        story.append(thin_rule())

    # ── Risques identifiés (sans tableau) ───────────────────────────────
    if risks:
        story += section_header("Risques identifiés", count=len(risks))
        sev_colors = {
            "élevé":  C_SEV_HAUT,
            "haut":   C_SEV_HAUT,
            "moyen":  C_SEV_MOYEN,
            "faible": C_SEV_FAIBLE,
        }
        for i, r in enumerate(risks, 1):
            sev_key = (r.severity or "").strip().lower()
            sev_color = sev_colors.get(sev_key, C_TAUPE)
            sev_hex = sev_color.hexval()[2:]

            if r.severity:
                header = (f'{i}. <font color="#{sev_hex}">[{escape(r.severity).upper()}]</font> '
                           f'{escape(r.content)}')
            else:
                header = f"{i}. {escape(r.content)}"

            block = [Paragraph(header, style_item_title)]
            if getattr(r, "mitigation", None):
                block.append(Paragraph(f"Atténuation : {escape(r.mitigation)}", style_item_note))
            block.append(Spacer(1, 0.15*cm))
            story.append(KeepTogether(block))
        story.append(thin_rule())

    # ── Conclusion ───────────────────────────────────────────────────────
    if summary and getattr(summary, "conclusion", None):
        story += section_header("Conclusion")
        story.append(Paragraph(escape(summary.conclusion), style_body))

    # ── Transcription complète (page séparée) ──────────────────────────
    if transcript and getattr(transcript, "full_text", None):
        story.append(PageBreak())
        story.append(Paragraph("Annexe — transcription complète", style_h1))
        story.append(HRFlowable(width="100%", thickness=1.1, color=C_BORDEAUX_SOFT,
                                 spaceBefore=0, spaceAfter=10))

        paragraphs = transcript.full_text.split("\n")
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(escape(para.strip()), style_transcript))

    # ── Pied de page ─────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_FILET_CLAIR))
    generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"Document généré automatiquement par l'Assistant IA de Réunion — {generated_at}",
        style_footer
    ))

    # ── Génération du PDF ────────────────────────────────────────────────
    doc.build(story)
    logger.info(f"PDF généré : {output_path}")
    return output_path
