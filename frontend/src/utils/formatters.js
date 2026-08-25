// Utilitaires de formatage partages dans toute l'application.

/**
 * Le backend renvoie des dates ISO sans indicateur de fuseau horaire
 * (ex: "2026-06-28T06:00:00.000000"), qui representent en realite un
 * instant UTC. Sans ce correctif, le navigateur les interprete comme une
 * heure locale et decale tous les affichages relatifs de la valeur du
 * fuseau local (par ex. "il y a 1h" juste apres la creation, pour un
 * utilisateur en UTC+1). On force donc explicitement l'UTC quand aucun
 * fuseau n'est present dans la chaine.
 */
function parseApiDate(iso) {
  if (!iso) return null;
  const hasZone = /Z$|[+-]\d{2}:?\d{2}$/.test(iso);
  const normalized = hasZone ? iso : `${iso}Z`;
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Formate une duree en secondes vers "1h 24min" ou "3min 12s". */
export function formatDuration(totalSeconds) {
  if (totalSeconds === null || totalSeconds === undefined) return '\u2014';
  const s = Math.max(0, Math.round(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}min`;
  if (m > 0) return `${m}min ${String(sec).padStart(2, '0')}s`;
  return `${sec}s`;
}

/** Formate une duree en compte-a-rebours mm:ss pour l'enregistrement. */
export function formatClock(totalSeconds) {
  const s = Math.max(0, Math.round(totalSeconds));
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

/** Formate un poids en octets vers "2,3 Mo". */
export function formatFileSize(bytes) {
  if (!bytes && bytes !== 0) return '\u2014';
  if (bytes < 1024) return `${bytes} o`;
  const ko = bytes / 1024;
  if (ko < 1024) return `${ko.toFixed(1).replace('.', ',')} Ko`;
  const mo = ko / 1024;
  return `${mo.toFixed(1).replace('.', ',')} Mo`;
}

/** Formate une date ISO vers "28 juin 2026". */
export function formatDate(iso) {
  const d = parseApiDate(iso);
  if (!d) return '\u2014';
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
}

/** Formate une date ISO vers "28/06/2026". */
export function formatDateShort(iso) {
  const d = parseApiDate(iso);
  if (!d) return '\u2014';
  return d.toLocaleDateString('fr-FR');
}

/** Formate une date ISO vers l'heure "14:32". */
export function formatTime(iso) {
  const d = parseApiDate(iso);
  if (!d) return '\u2014';
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

/** Formate une date ISO relative simple : "il y a 3h", "hier", etc. */
export function formatRelative(iso) {
  const d = parseApiDate(iso);
  if (!d) return '\u2014';
  const diffMs = Date.now() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "a l'instant";
  if (diffMin < 60) return `il y a ${diffMin}min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `il y a ${diffH}h`;
  const diffJ = Math.floor(diffH / 24);
  if (diffJ === 1) return 'hier';
  if (diffJ < 7) return `il y a ${diffJ}j`;
  return formatDateShort(iso);
}