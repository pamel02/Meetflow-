import { MEETING_STATUS_LABELS, PIPELINE_STEPS } from '../utils/status';

/**
 * Rail de progression signature de l'application : chaque etape du pipeline
 * est representee comme un segment qui chevauche legerement le suivant, en
 * echo direct au decoupage audio (segments de 60s, chevauchement de 5s) qui
 * est le mecanisme central du produit.
 */
export default function ProgressRail({ status, progressPercent = null, step = null }) {
  const isError = status === 'error';
  const currentIndex = isError ? -1 : PIPELINE_STEPS.indexOf(status);

  return (
    <div className="w-full">
      <div className="relative flex h-2 w-full overflow-hidden rounded-full bg-liseret">
        {PIPELINE_STEPS.map((s, i) => {
          const reached = !isError && i <= currentIndex;
          return (
            <div
              key={s}
              className={`h-full flex-1 ${reached ? 'bg-bordeaux-600' : 'bg-liseret'}`}
              title={MEETING_STATUS_LABELS[s]}
            />
          );
        })}
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde">
          {isError ? 'Erreur' : step || MEETING_STATUS_LABELS[status]}
        </span>
        {progressPercent !== null && (
          <span className="font-donnees text-[11px] text-encre-sourde">{progressPercent}%</span>
        )}
      </div>
    </div>
  );
}
