import { createPortal } from 'react-dom';
import Button from './Button';
import { formatClock, formatFileSize } from '../utils/formatters';

const WAVEFORM = [18, 26, 22, 34, 48, 30, 58, 72, 42, 28, 38, 64, 82, 48, 34, 54, 68, 88, 62, 42, 56, 46, 36, 26];

export default function RecordingOverlay({ recorder, onStop }) {
  const { recordingState, elapsedSeconds, segmentsCreated, estimatedBytes, pendingUploads, lastError, pause, resume } = recorder;
  if (recordingState !== 'recording' && recordingState !== 'paused') return null;

  return createPortal(
    <div role="dialog" aria-modal="true" aria-label="Réunion en cours" className="fixed inset-0 z-[100] flex min-h-dvh flex-col overflow-y-auto bg-fond">
      <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-liseret bg-white px-5 sm:px-8">
        <div className="flex items-center gap-4"><span className="text-lg font-extrabold tracking-[-0.03em] text-encre">MeetFlow</span><span className="h-6 w-px bg-liseret"/><span className="flex items-center gap-2 text-sm font-medium text-encre-douce"><span className={`h-2 w-2 rounded-full ${recordingState === 'recording' ? 'animate-pulse bg-red-500' : 'bg-amber-400'}`}/>{recordingState === 'recording' ? 'Enregistrement en cours' : 'En pause'}</span></div>
        <span className="hidden rounded-full border border-liseret bg-fond px-3 py-1.5 text-xs font-medium text-encre-sourde sm:block">Mode concentration</span>
      </header>

      <main className="relative flex flex-1 items-center justify-center overflow-hidden px-4 py-12">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(64,88,237,0.12),transparent_50%)]" />
        <div className="relative z-10 flex w-full max-w-4xl flex-col items-center text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-encre-sourde">Temps écoulé</p>
          <p className="mt-4 font-donnees text-6xl font-semibold tabular-nums tracking-[-0.07em] text-encre sm:text-8xl">{formatClock(elapsedSeconds)}</p>

          <div className="mt-12 flex h-24 items-center justify-center gap-1" aria-hidden="true">
            {WAVEFORM.map((height, index) => <span key={index} className={`w-1 rounded-full ${recordingState === 'recording' ? 'bg-bordeaux-600' : 'bg-taupe-400'}`} style={{ height: `${height}%`, opacity: 0.38 + (index % 5) * 0.14 }}/>) }
          </div>

          <div className="mt-12 grid w-full max-w-xl grid-cols-3 divide-x divide-liseret rounded-2xl border border-liseret bg-white px-4 py-4 shadow-[0_12px_40px_rgba(16,24,40,0.06)]">
            <Metric value={segmentsCreated} label="Segments" />
            <Metric value={formatFileSize(estimatedBytes)} label="Volume audio" />
            <Metric value={pendingUploads} label="En cours d’envoi" />
          </div>

          {lastError && <p className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">{lastError}</p>}

          <div className="mt-8 flex items-center justify-center gap-3">
            {recordingState === 'recording' ? <Button variant="secondary" size="lg" onClick={pause}>Mettre en pause</Button> : <Button variant="secondary" size="lg" onClick={resume}>Reprendre</Button>}
            <Button variant="recording" size="lg" onClick={onStop}><span className="h-3 w-3 rounded-sm bg-white"/>Arrêter l’enregistrement</Button>
          </div>
          <p className="mt-5 max-w-lg text-xs leading-relaxed text-encre-sourde">Les segments sont sauvegardés automatiquement pendant la réunion. Vous pouvez arrêter sans perdre les données déjà envoyées.</p>
        </div>
      </main>
    </div>,
    document.body
  );
}

function Metric({ value, label }) {
  return <div className="px-3"><p className="text-lg font-bold text-encre">{value}</p><p className="mt-1 text-[11px] font-medium text-encre-sourde">{label}</p></div>;
}
