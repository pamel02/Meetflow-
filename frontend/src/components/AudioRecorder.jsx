import Button from './Button';

/**
 * Ecran de demarrage affiche dans l'onglet "Enregistrement" tant que la
 * reunion est en attente. Une fois l'enregistrement demarre, le cadre actif
 * (temps ecoule, segments, Pause / Arreter) est pris en charge par
 * RecordingOverlay, qui verrouille le reste de l'application.
 */
export default function AudioRecorder({ recorder }) {
  const { micState, lastError, start } = recorder;

  return (
    <div className="flex flex-col items-center gap-5 rounded-2xl border border-bordeaux-400/50 bg-bordeaux-500/[0.025] px-6 py-14 text-center sm:px-8">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-bordeaux-700 text-white shadow-[0_12px_28px_rgba(38,59,216,0.25)]"><svg viewBox="0 0 24 24" className="h-9 w-9" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/></svg></div>
      <p className="font-display text-2xl font-semibold tracking-[-0.03em] text-encre">Prêt à enregistrer</p>
      <p className="max-w-md text-sm text-encre-sourde">
        L'enregistrement est decoupe automatiquement en segments de 60 secondes, envoyes au fur et a
        mesure, sans jamais garder plusieurs minutes d'audio en memoire. Une fois demarree, la reunion
        occupe tout l'ecran et le reste de l'application est verrouille jusqu'a l'arret.
      </p>
      {micState === 'denied' && (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {lastError || 'Acces au microphone refuse.'}
        </p>
      )}
      <Button size="lg" loading={micState === 'requesting'} onClick={start}>
        Démarrer la réunion
      </Button>
    </div>
  );
}
