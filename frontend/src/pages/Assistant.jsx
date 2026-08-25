import { useEffect, useState } from 'react';
import TopBar from '../components/TopBar';
import ChatBox from '../components/ChatBox';
import { chatService, meetingService } from '../services';

export default function Assistant() {
  const [meetings, setMeetings] = useState([]);
  const [scope, setScope] = useState('all');

  useEffect(() => {
    meetingService
      .list({ status: 'completed', sortBy: 'created_at', sortDir: 'desc' })
      .then((data) => setMeetings(data.meetings || []))
      .catch(() => setMeetings([]));
  }, []);

  const selectedMeeting = meetings.find((meeting) => String(meeting.id) === String(scope));
  const scopeLabel = selectedMeeting?.title || 'Toutes les réunions';

  const handleAsk = (question) => {
    if (scope === 'all') return chatService.ask(question);
    return chatService.askAbout(scope, question);
  };

  return (
    <>
      <TopBar title="Assistant IA" />
      <main className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-white">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-52 bg-[radial-gradient(circle_at_50%_0%,rgba(64,88,237,0.08),transparent_68%)]" />

        <div className="relative z-10 flex h-16 shrink-0 items-center justify-center border-b border-liseret/80 px-4">
          <div className="flex min-w-0 items-center gap-2 rounded-full border border-liseret bg-white px-3 py-1.5 shadow-sm">
            <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-bordeaux-600" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3M8 21H5a2 2 0 0 1-2-2v-3m18 0v3a2 2 0 0 1-2 2h-3" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <span className="hidden text-xs font-medium text-encre-sourde sm:inline">Source</span>
            <select
              value={scope}
              onChange={(event) => setScope(event.target.value)}
              aria-label="Choisir les réunions à interroger"
              className="max-w-[220px] truncate bg-transparent pr-1 text-xs font-semibold text-encre outline-none sm:max-w-[320px]"
            >
              <option value="all">Toutes les réunions</option>
              {meetings.map((meeting) => (
                <option key={meeting.id} value={meeting.id}>
                  {meeting.title || `Réunion #${meeting.id}`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <ChatBox
          key={scope}
          onAsk={handleAsk}
          scopeLabel={scopeLabel}
          placeholder={
            scope === 'all'
              ? 'Interrogez la mémoire de votre entreprise…'
              : 'Posez une question sur cette réunion…'
          }
        />
      </main>
    </>
  );
}
