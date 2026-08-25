import { Link } from 'react-router-dom';
import Button from './Button';
import StatusPill from './StatusPill';
import { MEETING_STATUS_LABELS, statusTone } from '../utils/status';
import { formatDate, formatDuration } from '../utils/formatters';

export default function MeetingTable({ meetings, onDelete, onDownloadPdf, onSort, sortBy, sortDir }) {
  const headerButton = (key, label) => (
    <button
      onClick={() => onSort?.(key)}
      className="flex items-center gap-1 font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde hover:text-encre"
    >
      {label}
      {sortBy === key && <span aria-hidden="true">{sortDir === 'asc' ? '\u2191' : '\u2193'}</span>}
    </button>
  );

  if (!meetings.length) {
    return (
      <div className="rounded-2xl border border-liseret bg-surface px-6 py-14 text-center shadow-sm">
        <p className="font-display text-lg text-encre">Aucune reunion ne correspond a ces criteres</p>
        <p className="mt-1 text-sm text-encre-sourde">Ajustez la recherche, le statut ou la periode.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-liseret bg-surface shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
      <table className="w-full min-w-[860px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-liseret bg-fond-doux text-left">
            <th className="px-4 py-3">{headerButton('title', 'Titre')}</th>
            <th className="px-4 py-3">{headerButton('created_at', 'Date')}</th>
            <th className="px-4 py-3">{headerButton('duration', 'Duree')}</th>
            <th className="px-4 py-3">Statut</th>
            <th className="px-4 py-3">Segments</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {meetings.map((m) => (
            <tr key={m.id} className="border-b border-liseret transition-colors last:border-b-0 hover:bg-bordeaux-500/[0.025]">
              <td className="max-w-[260px] truncate px-4 py-3 text-encre">
                {m.title || <span className="text-encre-sourde">Titre en attente</span>}
              </td>
              <td className="px-4 py-3 font-donnees text-xs text-encre-sourde">{formatDate(m.created_at)}</td>
              <td className="px-4 py-3 font-donnees text-xs text-encre-sourde">{formatDuration(m.duration)}</td>
              <td className="px-4 py-3">
                <StatusPill label={MEETING_STATUS_LABELS[m.status]} tone={statusTone(m.status)} />
              </td>
              <td className="px-4 py-3 font-donnees text-xs text-encre-sourde">{m.segments_count ?? 0}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <Link to={`/reunions/${m.id}`}>
                    <Button variant="secondary" size="sm">Ouvrir</Button>
                  </Link>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={m.status !== 'completed'}
                    onClick={() => onDownloadPdf?.(m)}
                  >
                    PDF
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => onDelete?.(m)}>
                    Supprimer
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
