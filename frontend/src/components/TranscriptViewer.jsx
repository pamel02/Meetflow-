export default function TranscriptViewer({ transcript, pending }) {
  if (pending) {
    return (
      <p className="py-8 text-center text-sm text-encre-sourde">
        La transcription est encore en cours de traitement. Cette section se mettra a jour automatiquement.
      </p>
    );
  }

  if (!transcript?.full_text) {
    return <p className="py-8 text-center text-sm text-encre-sourde">Aucune transcription disponible.</p>;
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-3 font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde">
        <span>Langue detectee : {transcript.language || 'inconnue'}</span>
      </div>
      <p className="whitespace-pre-line text-sm leading-relaxed text-encre-douce">{transcript.full_text}</p>
    </div>
  );
}
