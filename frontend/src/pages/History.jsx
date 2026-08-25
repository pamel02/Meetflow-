import { useCallback, useEffect, useState } from 'react';
import TopBar from '../components/TopBar';
import MeetingTable from '../components/MeetingTable';
import Input from '../components/Input';
import { Loader } from '../components/Loader';
import { meetingService, exportService } from '../services';
import { useToast } from '../context/ToastContext';
import { MEETING_STATUS_LABELS } from '../utils/status';

export default function History() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');
  const { notify } = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await meetingService.list({ search, status, sortBy, sortDir });
      setMeetings(data.meetings);
    } catch (err) {
      notify.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [search, status, sortBy, sortDir, notify]);

  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  const handleSort = (key) => {
    if (sortBy === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(key);
      setSortDir('asc');
    }
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
      <TopBar title="Réunions" />
      <main className="flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8">
        <div className="mx-auto w-full max-w-[1480px]">
        <div className="mb-7"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Mémoire d’entreprise</p><h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre">Toutes les réunions</h2><p className="mt-2 text-sm text-encre-sourde">Retrouvez rapidement un échange, son rapport et ses décisions.</p></div>
        <div className="mb-6 flex flex-wrap gap-3 rounded-2xl border border-liseret bg-white p-4 shadow-sm">
          <div className="min-w-[220px] flex-1">
            <Input
              placeholder="Rechercher un titre ou une description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-xl border border-liseret bg-white px-3.5 py-2.5 text-sm text-encre shadow-sm focus:border-bordeaux-500"
          >
            <option value="">Tous les statuts</option>
            {Object.entries(MEETING_STATUS_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <Loader label="Recherche en cours..." />
        ) : (
          <MeetingTable
            meetings={meetings}
            onDelete={handleDelete}
            onDownloadPdf={handleDownloadPdf}
            onSort={handleSort}
            sortBy={sortBy}
            sortDir={sortDir}
          />
        )}
        </div>
      </main>
    </>
  );
}
