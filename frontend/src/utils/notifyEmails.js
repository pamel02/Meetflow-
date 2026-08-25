// Retient, cote client, les adresses email a notifier automatiquement des
// que le PDF d'une reunion devient disponible. Le backend n'ayant pas de
// champ dedie a la creation de la reunion, ce mapping est stocke localement
// et exploite par la page de detail : des que le statut passe a "completed",
// l'envoi est declenche automatiquement via POST /api/export/send-report.

const STORAGE_KEY = 'reunion_ia_notify_emails';

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeAll(map) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  } catch {
    // Stockage indisponible (navigation privee, quota...) : on ignore silencieusement.
  }
}

export function saveNotifyEmails(meetingId, emails) {
  if (!emails || emails.length === 0) return;
  const map = readAll();
  map[String(meetingId)] = emails;
  writeAll(map);
}

export function getNotifyEmails(meetingId) {
  const map = readAll();
  return map[String(meetingId)] || null;
}

export function clearNotifyEmails(meetingId) {
  const map = readAll();
  delete map[String(meetingId)];
  writeAll(map);
}
