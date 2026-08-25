import { Link } from 'react-router-dom';
import Button from './Button';
import Card from './Card';
import StatusPill from './StatusPill';
import { MEETING_STATUS_LABELS, statusTone } from '../utils/status';
import { formatDate, formatDuration, formatTime } from '../utils/formatters';

export default function MeetingCard({ meeting, onDelete, onDownloadPdf }) {
  const canDownload = meeting.status === 'completed';

  return (
    <Card className="group flex flex-col gap-4 p-5 transition duration-200 hover:-translate-y-0.5 hover:border-bordeaux-400/60 hover:shadow-[0_16px_40px_rgba(16,24,40,0.08)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-encre-sourde">
            {formatDate(meeting.created_at)} · {formatTime(meeting.created_at)}
          </p>
          <h3 className="mt-1.5 truncate font-display text-lg font-semibold tracking-[-0.02em] text-encre">
            {meeting.title || 'Titre en attente de generation'}
          </h3>
          {meeting.description && (
            <p className="mt-1 line-clamp-2 text-sm text-encre-douce">{meeting.description}</p>
          )}
        </div>
        <StatusPill label={MEETING_STATUS_LABELS[meeting.status]} tone={statusTone(meeting.status)} />
      </div>

      <div className="flex items-center gap-5 border-t border-liseret pt-3 text-xs font-medium text-encre-sourde">
        <span>Duree {formatDuration(meeting.duration)}</span>
        <span>{meeting.segments_count ?? 0} segments</span>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link to={`/reunions/${meeting.id}`}>
          <Button variant="primary" size="sm">Ouvrir</Button>
        </Link>
        {meeting.status === 'completed' && (
          <Link to={`/reunions/${meeting.id}?onglet=compte-rendu`}>
            <Button variant="secondary" size="sm">Voir le compte rendu</Button>
          </Link>
        )}
        <Button variant="secondary" size="sm" disabled={!canDownload} onClick={() => onDownloadPdf?.(meeting)}>
          Telecharger le PDF
        </Button>
        {onDelete && <Button variant="danger" size="sm" onClick={() => onDelete(meeting)}>
          Supprimer
        </Button>}
      </div>
    </Card>
  );
}
