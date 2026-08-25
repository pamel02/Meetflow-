import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import TopBar from '../components/TopBar';
import Card, { CardHeader } from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import StatusPill from '../components/StatusPill';
import ProgressRail from '../components/ProgressRail';
import AudioRecorder from '../components/AudioRecorder';
import RecordingOverlay from '../components/RecordingOverlay';
import TranscriptViewer from '../components/TranscriptViewer';
import SummaryViewer from '../components/SummaryViewer';
import SendReportPanel from '../components/SendReportPanel';
import EmailChipsField from '../components/EmailChipsField';
import { Loader, SkeletonBlock } from '../components/Loader';
import { meetingService, aiDataService, audioService, exportService, loadSegmentPlaybackUrl } from '../services';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useMeetingStatus } from '../hooks/useMeetingStatus';
import { useToast } from '../context/ToastContext';
import { MEETING_STATUS_LABELS, SEGMENT_STATUS_LABELS, statusTone } from '../utils/status';
import { formatDate, formatDuration, formatFileSize, formatTime } from '../utils/formatters';
import { saveNotifyEmails, getNotifyEmails, clearNotifyEmails } from '../utils/notifyEmails';

const TABS = [
  { key: 'informations', label: 'Informations' },
  { key: 'enregistrement', label: 'Enregistrement' },
  { key: 'transcription', label: 'Transcription' },
  { key: 'compte-rendu', label: 'Compte rendu IA' },
  { key: 'segments', label: 'Segments audio' },
];

export default function MeetingDetail() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('onglet') || 'informations';
  const navigate = useNavigate();
  const { notify } = useToast();

  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  const [segmentsData, setSegmentsData] = useState(null);
  const [segmentsLoading, setSegmentsLoading] = useState(false);

  const [notifyEmails, setNotifyEmails] = useState(() => getNotifyEmails(id) || []);
  const autoSendTriggeredRef = useRef(false);

  const recorder = useAudioRecorder(id);

  const loadMeeting = useCallback(async () => {
    try {
      const data = await meetingService.get(id);
      setMeeting(data.meeting);
      setLoadError(null);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadMeeting();
  }, [loadMeeting]);

  const isProcessing = meeting && !['completed', 'error', 'pending'].includes(meeting.status);
  const { progress } = useMeetingStatus(id, { active: Boolean(isProcessing) });

  useEffect(() => {
    if (progress?.status === 'completed' && meeting?.status !== 'completed') {
      loadMeeting();
    }
    if (progress && progress.status !== meeting?.status) {
      setMeeting((m) => (m ? { ...m, status: progress.status } : m));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progress]);

  // Envoi automatique du PDF des que la reunion est terminee, si des
  // destinataires ont ete renseignes a la creation (voir NewMeetingModal).
  useEffect(() => {
    if (
      meeting?.status === 'completed' &&
      notifyEmails.length > 0 &&
      !autoSendTriggeredRef.current
    ) {
      autoSendTriggeredRef.current = true;
      exportService
        .sendReport(id, notifyEmails, 'Compte rendu de reunion')
        .then(() => {
          notify.success(
            `Compte rendu envoye automatiquement a ${notifyEmails.length} destinataire(s).`
          );
          clearNotifyEmails(id);
          setNotifyEmails([]);
        })
        .catch((err) => {
          notify.error(`Envoi automatique du compte rendu impossible : ${err.message}`);
        });
    }
  }, [meeting?.status, notifyEmails, id, notify]);

  const setTab = (key) => setSearchParams({ onglet: key });

  const loadReport = useCallback(async () => {
    setReportLoading(true);
    try {
      const data = await aiDataService.report(id);
      setReport(data);
    } catch (err) {
      notify.error(err.message);
    } finally {
      setReportLoading(false);
    }
  }, [id, notify]);

  const loadSegments = useCallback(async () => {
    setSegmentsLoading(true);
    try {
      const data = await audioService.status(id);
      setSegmentsData(data);
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSegmentsLoading(false);
    }
  }, [id, notify]);

  useEffect(() => {
    if (activeTab === 'compte-rendu' && meeting?.status === 'completed' && !report) loadReport();
    if (activeTab === 'segments') loadSegments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, meeting?.status]);

  const handleStopRecording = async () => {
    try {
      await recorder.stop();
      notify.success("Enregistrement termine. Le traitement du bilan va commencer.");
      loadMeeting();
      setTab('informations');
    } catch {
      notify.error("Impossible de signaler la fin de la reunion au serveur.");
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Supprimer definitivement cette reunion et toutes ses donnees ?')) return;
    try {
      await meetingService.remove(id);
      clearNotifyEmails(id);
      notify.success('Reunion supprimee.');
      navigate('/app');
    } catch (err) {
      notify.error(err.message);
    }
  };

  const handleReprocess = async () => {
    try {
      await meetingService.reprocess(id);
      notify.success('Retraitement lance.');
      loadMeeting();
    } catch (err) {
      notify.error(err.message);
    }
  };

  const handleDownloadPdf = async (includeTranscript = false) => {
    try {
      await exportService.downloadPdf(id, includeTranscript);
    } catch (err) {
      notify.error(err.message);
    }
  };

  const handleExportJson = async () => {
    try {
      const data = await exportService.exportJson(id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reunion_${id}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      notify.error(err.message);
    }
  };

  const handleUpdateNotifyEmails = (emails) => {
    setNotifyEmails(emails);
    if (emails.length > 0) saveNotifyEmails(id, emails);
    else clearNotifyEmails(id);
  };

  if (loading) {
    return (
      <>
        <TopBar title="Reunion" />
        <main className="flex-1 px-4 py-6 sm:px-6 md:px-8">
          <Loader label="Chargement de la reunion..." />
        </main>
      </>
    );
  }

  if (loadError || !meeting) {
    return (
      <>
        <TopBar title="Reunion introuvable" />
        <main className="flex-1 px-4 py-10 sm:px-6 md:px-8">
          <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-6 text-red-700">
            <p className="font-display text-lg">Reunion introuvable</p>
            <p className="mt-1 text-sm text-encre-douce">{loadError || "Cette reunion n'existe pas ou vous n'y avez pas acces."}</p>
            <Button className="mt-4" variant="secondary" onClick={() => navigate('/app')}>
              Retour au tableau de bord
            </Button>
          </div>
        </main>
      </>
    );
  }

  const reportReady = meeting.status === 'completed';

  return (
    <>
      <RecordingOverlay recorder={recorder} onStop={handleStopRecording} />
      <TopBar title={meeting.title || 'Reunion sans titre'} />
      <main className="min-h-0 flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8">
        <div className="mx-auto w-full max-w-[1480px]">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-liseret bg-white px-5 py-4 shadow-sm">
          <div className="flex items-center gap-3">
            <StatusPill label={MEETING_STATUS_LABELS[meeting.status]} tone={statusTone(meeting.status)} />
            <span className="font-donnees text-xs text-encre-sourde">
              {formatDate(meeting.created_at)} · {formatTime(meeting.created_at)}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" disabled={meeting.status !== 'completed'} onClick={() => handleDownloadPdf(false)}>
              Télécharger le rapport
            </Button>
            <Button variant="ghost" size="sm" disabled={meeting.status !== 'completed'} onClick={() => handleDownloadPdf(true)}>
              Rapport + transcription
            </Button>
            <Button variant="secondary" size="sm" disabled={meeting.status !== 'completed'} onClick={handleExportJson}>
              Exporter en JSON
            </Button>
            <Button variant="secondary" size="sm" disabled={meeting.status !== 'completed'} onClick={handleReprocess}>
              Retraiter
            </Button>
            <Button variant="danger" size="sm" onClick={handleDelete}>Supprimer</Button>
          </div>
        </div>

        {isProcessing && (
          <Card className="mb-6 px-5 py-4">
            <ProgressRail status={progress?.status || meeting.status} progressPercent={progress?.progress} step={progress?.step} />
          </Card>
        )}

        <div className="mb-6 flex gap-1 overflow-x-auto rounded-xl border border-liseret bg-white p-1 shadow-sm">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition ${
                activeTab === t.key
                  ? 'bg-bordeaux-500/10 text-bordeaux-700'
                  : 'text-encre-sourde hover:bg-surface-haute hover:text-encre'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === 'informations' && (
          <div className="flex flex-col gap-6">
            <InformationsTab meeting={meeting} onSaved={setMeeting} />
            <NotifyEmailsCard
              emails={notifyEmails}
              onChange={handleUpdateNotifyEmails}
              sent={meeting.status === 'completed' && notifyEmails.length === 0 && autoSendTriggeredRef.current}
            />
          </div>
        )}

        {activeTab === 'enregistrement' && (
          <Card className="p-6">
            {meeting.status === 'pending' ? (
              recorder.recordingState === 'idle' ? (
                <AudioRecorder recorder={{ ...recorder, stop: handleStopRecording }} />
              ) : (
                <p className="py-8 text-center text-sm text-encre-sourde">
                  Enregistrement en cours. Le cadre affiche a l'ecran permet de le mettre en pause ou de
                  l'arreter.
                </p>
              )
            ) : (
              <p className="py-8 text-center text-sm text-encre-sourde">
                Cette reunion n'est plus en attente d'enregistrement (statut actuel :{' '}
                {MEETING_STATUS_LABELS[meeting.status]}).
              </p>
            )}
          </Card>
        )}

        {activeTab === 'transcription' && (
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_320px]">
            <Card className="p-6">
              <TranscriptTab meetingId={id} status={meeting.status} />
            </Card>
            <SendReportPanel meetingId={id} ready={reportReady} />
          </div>
        )}

        {activeTab === 'compte-rendu' && (
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_320px]">
            {reportLoading ? (
              <Loader label="Chargement du compte rendu..." />
            ) : (
              <SummaryViewer report={report} pending={meeting.status !== 'completed'} />
            )}
            <SendReportPanel meetingId={id} ready={reportReady} />
          </div>
        )}

        {activeTab === 'segments' && (
          <SegmentsTab
            loading={segmentsLoading}
            data={segmentsData}
            localSegments={recorder.localSegments}
            onRefresh={loadSegments}
          />
        )}
        </div>
      </main>
    </>
  );
}

function NotifyEmailsCard({ emails, onChange, sent }) {
  return (
    <Card>
      <CardHeader
        eyebrow="Envoi automatique"
        title="Destinataires du compte rendu"
      />
      <div className="px-5 py-5">
        <p className="mb-4 text-xs text-encre-sourde">
          Ces adresses recevront automatiquement le PDF du compte rendu des qu'il sera pret. Vous pouvez
          en ajouter ou en retirer tant que la reunion n'est pas terminee.
        </p>
        {sent && (
          <p className="mb-4 border border-liseret-clair bg-fond-doux px-3 py-2 text-xs text-encre-douce">
            Le compte rendu a deja ete envoye aux destinataires programmes.
          </p>
        )}
        <EmailChipsField emails={emails} onChange={onChange} />
      </div>
    </Card>
  );
}

function InformationsTab({ meeting, onSaved }) {
  const [title, setTitle] = useState(meeting.title || '');
  const [description, setDescription] = useState(meeting.description || '');
  const [saving, setSaving] = useState(false);
  const { notify } = useToast();

  const dirty = title !== (meeting.title || '') || description !== (meeting.description || '');

  const handleSave = async () => {
    setSaving(true);
    try {
      const data = await meetingService.update(meeting.id, { title, description });
      onSaved(data.meeting);
      notify.success('Reunion mise a jour.');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader eyebrow="Details" title="Informations de la reunion" />
      <div className="grid grid-cols-1 gap-5 px-5 py-5 md:grid-cols-2">
        <Input label="Titre" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Titre genere automatiquement si vide" />
        <label className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-encre-douce">Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="resize-none rounded-xl border border-liseret bg-white px-3.5 py-3 text-sm text-encre shadow-sm focus:border-bordeaux-500"
          />
        </label>
        <div className="grid grid-cols-2 gap-4 md:col-span-2 md:grid-cols-4">
          <InfoField label="Date" value={formatDate(meeting.created_at)} />
          <InfoField label="Duree" value={formatDuration(meeting.duration)} />
          <InfoField label="Segments" value={meeting.segments_count ?? 0} />
          <InfoField label="Statut" value={MEETING_STATUS_LABELS[meeting.status]} />
        </div>
        {meeting.error_message && (
          <div className="md:col-span-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {meeting.error_message}
          </div>
        )}
        <div className="md:col-span-2">
          <Button disabled={!dirty} loading={saving} onClick={handleSave}>
            Enregistrer les modifications
          </Button>
        </div>
      </div>
    </Card>
  );
}

function InfoField({ label, value }) {
  return (
    <div>
      <p className="font-donnees text-[10px] uppercase tracking-[0.1em] text-encre-sourde">{label}</p>
      <p className="mt-1 text-sm text-encre">{value}</p>
    </div>
  );
}

function TranscriptTab({ meetingId, status }) {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(status !== 'completed');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const data = await aiDataService.transcript(meetingId);
        if (!cancelled) {
          setTranscript(data.transcript);
          setPending(false);
        }
      } catch (err) {
        if (!cancelled && err.status === 202) setPending(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [meetingId, status]);

  if (loading) return <SkeletonBlock className="h-40" />;
  return <TranscriptViewer transcript={transcript} pending={pending} />;
}

function SegmentsTab({ loading, data, localSegments = [], onRefresh }) {
  if (loading && !data) return <Loader label="Chargement des segments..." />;
  if (!data) return null;

  // On privilegie la copie locale (disponible immediatement, y compris pendant
  // l'enregistrement) et on retombe sur une URL serveur reconstruite sinon.
  const localByNumber = new Map(localSegments.map((s) => [s.segmentNumber, s.url]));
  const orderedSegments = [...data.segments].sort((a, b) => a.segment_number - b.segment_number);

  return (
    <Card>
      <CardHeader
        eyebrow={`${data.segments_count} segment(s)`}
        title="Fichiers audio envoyes, dans l'ordre"
        action={
          <Button variant="secondary" size="sm" onClick={onRefresh}>
            Actualiser
          </Button>
        }
      />
      <div className="flex gap-6 border-b border-liseret px-5 py-3 font-donnees text-xs text-encre-sourde">
        <span>Transcrits : {data.transcribed_count}</span>
        <span>En attente : {data.pending_count}</span>
      </div>
      <ul className="divide-y divide-liseret">
        {orderedSegments.map((s) => {
          const localUrl = localByNumber.get(s.segment_number);
          return (
            <li key={s.id} className="flex flex-wrap items-center gap-4 px-5 py-3">
              <span className="w-12 font-donnees text-sm text-encre">#{s.segment_number}</span>
              <span className="w-20 font-donnees text-xs text-encre-sourde">{formatTime(s.received_at)}</span>
              <span className="w-24 font-donnees text-xs text-encre-sourde">{formatDuration(s.duration)}</span>
              <span className="w-20 font-donnees text-xs text-encre-sourde">{formatFileSize(s.file_size)}</span>
              <StatusPill
                label={SEGMENT_STATUS_LABELS[s.status] || s.status}
                tone={s.status === 'error' ? 'border-bordeaux-500 text-encre' : 'border-liseret-clair text-encre-sourde'}
              />
              <div className="ml-auto min-w-[220px] flex-1">
                <SegmentPlayer localSrc={localUrl} filename={s.filename} />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function SegmentPlayer({ localSrc, filename }) {
  const [failed, setFailed] = useState(false);
  const [remoteSrc, setRemoteSrc] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    return () => {
      if (remoteSrc) URL.revokeObjectURL(remoteSrc);
    };
  }, [remoteSrc]);

  const loadRemote = async () => {
    setLoading(true);
    try {
      setRemoteSrc(await loadSegmentPlaybackUrl(filename));
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  };

  const src = localSrc || remoteSrc;

  if (failed || (!src && !filename)) {
    return (
      <p className="text-right font-donnees text-[11px] text-encre-sourde">
        Lecture indisponible pour ce segment.
      </p>
    );
  }

  if (!src) {
    return (
      <Button variant="secondary" size="sm" onClick={loadRemote} disabled={loading}>
        {loading ? 'Chargement...' : 'Charger l’audio'}
      </Button>
    );
  }

  return (
    <audio
      controls
      preload="none"
      src={src}
      onError={() => setFailed(true)}
      className="h-9 w-full"
    />
  );
}
