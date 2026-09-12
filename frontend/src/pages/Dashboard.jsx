import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import TopBar from '../components/TopBar';
import StatCard from '../components/StatCard';
import MeetingCard from '../components/MeetingCard';
import NewMeetingModal from '../components/NewMeetingModal';
import Button from '../components/Button';
import { Loader, SkeletonBlock } from '../components/Loader';
import { meetingService, exportService, billingService } from '../services';
import { useToast } from '../context/ToastContext';
import { formatDuration, formatRelative } from '../utils/formatters';
import { saveNotifyEmails } from '../utils/notifyEmails';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [billing, setBilling] = useState(null);
  const { notify } = useToast();
  const { user } = useAuth();
  const canOrganize = ['admin', 'organizer'].includes(user?.organization_role);
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const closeNewMeeting = () => {
    setModalOpen(false);
    if (searchParams.has('nouvelle')) setSearchParams({}, { replace: true });
  };

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [statsData, meetingsData, billingData] = await Promise.all([
        meetingService.stats(),
        meetingService.list({ sortBy: 'created_at', sortDir: 'desc' }),
        billingService.current(),
      ]);
      setStats(statsData.stats);
      setMeetings(meetingsData.meetings);
      setBilling(billingData);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (searchParams.get('nouvelle') === '1' && canOrganize) setModalOpen(true);
  }, [searchParams, canOrganize]);

  const [creatingQuick, setCreatingQuick] = useState(false);

  const handleQuickMeeting = async () => {
    setCreatingQuick(true);
    try {
      const now = new Date();
      const dateStr = now.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
      const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      const defaultTitle = `Point du ${dateStr} à ${timeStr}`;

      const data = await meetingService.create(defaultTitle, '');
      navigate(`/reunions/${data.meeting.id}?onglet=enregistrement&demarrer=1`);
    } catch (error) {
      if (error.status === 402) {
        navigate('/facturation', { state: { subscriptionRequired: true, from: '/app' } });
        return;
      }
      notify.error(error.message || 'Impossible de créer la réunion rapide.');
    } finally {
      setCreatingQuick(false);
    }
  };

  const handleCreate = async (title, description, notifyEmails = []) => {
    let data;
    try {
      data = await meetingService.create(title, description);
    } catch (error) {
      if (error.status === 402) {
        closeNewMeeting();
        navigate('/facturation', { state: { subscriptionRequired: true, from: '/app' } });
        return;
      }
      throw error;
    }
    if (notifyEmails.length > 0) {
      saveNotifyEmails(data.meeting.id, notifyEmails);
    }
    closeNewMeeting();
    navigate(`/reunions/${data.meeting.id}?onglet=enregistrement&demarrer=1`);
  };

  const handleDelete = async (meeting) => {
    if (!window.confirm(`Supprimer definitivement "${meeting.title || 'cette reunion'}" ?`)) return;
    try {
      await meetingService.remove(meeting.id);
      setMeetings((prev) => prev.filter((m) => m.id !== meeting.id));
      notify.success('Reunion supprimee.');
    } catch (err) {
      notify.error(err.message);
    }
  };

  const handleDownloadPdf = async (meeting) => {
    try {
      await exportService.downloadPdf(meeting.id);
    } catch (err) {
      notify.error(err.message);
    }
  };

  return (
    <>
      <TopBar title="Vue d’ensemble" />
      <main className="min-h-0 flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8">
        <div className="mx-auto w-full max-w-[1480px]">
        {!loading && !billing?.subscription && <div className="mb-6 flex flex-col gap-4 rounded-2xl border border-bordeaux-400/30 bg-gradient-to-r from-bordeaux-500/8 to-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-bold text-encre">{billing?.usage?.trial_meeting_available ? '4 000 minutes d’essai gratuit incluses' : 'Votre quota gratuit est utilisé'}</p><p className="mt-1 text-xs leading-relaxed text-encre-sourde">{billing?.usage?.trial_meeting_available ? 'Enregistrez vos réunions immédiatement, vos comptes rendus et bilans IA sont générés automatiquement.' : 'Choisissez une offre pour renouveler vos minutes de transcription.'}</p></div>{billing?.usage?.trial_meeting_available ? <Button size="sm" loading={creatingQuick} onClick={handleQuickMeeting}>⚡ Lancer ma première réunion</Button> : <Button size="sm" onClick={() => navigate('/facturation')}>Voir les offres</Button>}</div>}
        <div className="mb-8 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Espace de travail</p>
            <h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre sm:text-4xl">Pilotez vos réunions</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-encre-sourde">Enregistrez en 1 clic, laissez l’IA structurer vos échanges et téléchargez vos comptes rendus.</p>
          </div>
          {canOrganize && (
            <div className="flex flex-wrap items-center gap-3">
              <Button size="lg" loading={creatingQuick} onClick={handleQuickMeeting}>
                <span className="text-lg leading-none">⚡</span> Réunion Rapide (1 Clic)
              </Button>
              <Button size="lg" variant="secondary" onClick={() => setModalOpen(true)}>
                <span className="text-lg leading-none">+</span> Planifier
              </Button>
            </div>
          )}
        </div>
        {loadError && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {loadError}{' '}
            <button onClick={load} className="underline underline-offset-4">
              Reessayer
            </button>
          </div>
        )}

        <div className="mb-9 grid grid-cols-2 gap-4 lg:grid-cols-5">
          {loading && !stats
            ? Array.from({ length: 5 }).map((_, i) => <SkeletonBlock key={i} className="h-24" />)
            : stats && (
                <>
                  <StatCard label="Total reunions" value={stats.total} />
                  <StatCard label="Terminees" value={stats.completed} />
                  <StatCard label="En traitement" value={stats.processing} />
                  <StatCard
                    label="Duree moyenne"
                    value={formatDuration(stats.total > 0 ? stats.total_duration / stats.total : 0)}
                  />
                  <StatCard
                    label="Derniere reunion"
                    value={stats.last_meeting_at ? formatRelative(stats.last_meeting_at) : '\u2014'}
                  />
                </>
              )}
        </div>

        <div className="mb-5 flex items-end justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[0.1em] text-encre-sourde">Activité récente</p><h2 className="mt-1 text-xl font-semibold tracking-[-0.02em] text-encre">Vos réunions</h2></div>
          <span className="rounded-full border border-liseret bg-white px-3 py-1.5 text-xs font-medium text-encre-sourde">{meetings.length} au total</span>
        </div>

        {loading ? (
          <Loader label="Chargement des reunions..." />
        ) : meetings.length === 0 ? (
          <div className="rounded-2xl border border-liseret bg-surface px-6 py-16 text-center shadow-sm">
            <p className="font-display text-lg font-bold text-encre">Aucune réunion pour le moment</p>
            <p className="mt-1 text-sm text-encre-sourde">
              Démarrez un premier enregistrement en 1 clic pour tester l'intelligence MeetFlow.
            </p>
            {canOrganize && (
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                <Button size="lg" loading={creatingQuick} onClick={handleQuickMeeting}>
                  <span className="text-lg leading-none">⚡</span> Lancer ma première réunion
                </Button>
                <Button size="lg" variant="secondary" onClick={() => setModalOpen(true)}>
                  + Planifier
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {meetings.map((m) => (
              <MeetingCard key={m.id} meeting={m} onDelete={canOrganize ? handleDelete : undefined} onDownloadPdf={handleDownloadPdf} />
            ))}
          </div>
        )}
        </div>
      </main>

      {canOrganize && <NewMeetingModal open={modalOpen} onClose={closeNewMeeting} onCreate={handleCreate} />}
    </>
  );
}
