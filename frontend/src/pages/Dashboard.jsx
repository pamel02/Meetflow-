import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import TopBar from '../components/TopBar';
import StatCard from '../components/StatCard';
import MeetingCard from '../components/MeetingCard';
import NewMeetingModal from '../components/NewMeetingModal';
import Button from '../components/Button';
import { Loader, SkeletonBlock } from '../components/Loader';
import { meetingService, exportService } from '../services';
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
      const [statsData, meetingsData] = await Promise.all([
        meetingService.stats(),
        meetingService.list({ sortBy: 'created_at', sortDir: 'desc' }),
      ]);
      setStats(statsData.stats);
      setMeetings(meetingsData.meetings);
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

  const handleCreate = async (title, description, notifyEmails = []) => {
    const data = await meetingService.create(title, description);
    if (notifyEmails.length > 0) {
      saveNotifyEmails(data.meeting.id, notifyEmails);
    }
    closeNewMeeting();
    navigate(`/reunions/${data.meeting.id}`);
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
        <div className="mb-8 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Espace de travail</p>
            <h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre sm:text-4xl">Pilotez vos réunions</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-encre-sourde">Enregistrez, transcrivez et transformez chaque échange en décisions directement exploitables.</p>
          </div>
          {canOrganize && <Button size="lg" onClick={() => setModalOpen(true)}><span className="text-lg leading-none">+</span> Nouvelle réunion</Button>}
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
            <p className="font-display text-lg text-encre">Aucune reunion pour le moment</p>
            <p className="mt-1 text-sm text-encre-sourde">
              Creez votre premiere reunion pour demarrer un enregistrement.
            </p>
            {canOrganize && <Button className="mt-5" onClick={() => setModalOpen(true)}>Nouvelle reunion</Button>}
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
