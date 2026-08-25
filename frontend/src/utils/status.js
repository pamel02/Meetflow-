// Correspondances entre les statuts renvoyes par l'API et leur presentation.

export const MEETING_STATUS_LABELS = {
  pending: 'En attente',
  recording: 'Enregistrement',
  transcribing: 'Transcription',
  analyzing: 'Analyse IA',
  completed: 'Terminee',
  error: 'Erreur',
};

// Ordre du pipeline, utilise pour la barre de progression segmentee (composant signature).
export const PIPELINE_STEPS = ['pending', 'recording', 'transcribing', 'analyzing', 'completed'];

export const SEGMENT_STATUS_LABELS = {
  received: 'Recu',
  processing: 'En cours',
  transcribed: 'Transcrit',
  error: 'Echec',
};

export const SEVERITY_LABELS = {
  'élevé': 'Élevé',
  'eleve': 'Élevé',
  moyen: 'Moyen',
  faible: 'Faible',
};

/** Renvoie une classe Tailwind lisible sur les surfaces claires de l'application. */
export function statusTone(status) {
  switch (status) {
    case 'completed':
      return 'text-emerald-700 border-emerald-200 bg-emerald-50';
    case 'error':
      return 'text-red-700 border-red-200 bg-red-50';
    case 'analyzing':
    case 'transcribing':
    case 'recording':
      return 'text-bordeaux-700 border-bordeaux-400/40 bg-bordeaux-500/5';
    default:
      return 'text-encre-sourde border-liseret-clair bg-surface-haute';
  }
}

export function severityTone(severity) {
  const s = (severity || '').toLowerCase();
  if (s.includes('lev') || s.includes('elev')) return 'border-red-400 text-red-700';
  if (s.includes('moy')) return 'border-amber-400 text-amber-700';
  return 'border-liseret-clair text-encre-sourde';
}
