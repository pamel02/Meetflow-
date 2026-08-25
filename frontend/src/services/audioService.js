// Domaine 3 - Audio (3 endpoints)
import { http } from './httpClient';

/**
 * Construit une URL de lecture pour un segment deja envoye au serveur.
 * Le backend expose maintenant un endpoint dedie : /api/audio/file/{meeting_id}/{filename}
 * Le filename du DB contient le chemin complet : "uploads/meeting_N/segment_XXX.webm"
 * On extrait le meeting_id et le nom du fichier pour construire l'URL correcte.
 */
function buildSegmentPlaybackPath(filename) {
  if (!filename) return null;
  
  // Extrait meeting_id et filename depuis "uploads/meeting_9/segment_0000.webm"
  const match = filename.match(/uploads\/meeting_(\d+)\/(.+)$/);
  if (!match) return null;
  
  const [, meetingId, segmentFilename] = match;
  return `/api/audio/file/${meetingId}/${segmentFilename}`;
}

export async function loadSegmentPlaybackUrl(filename) {
  const path = buildSegmentPlaybackPath(filename);
  if (!path) return null;
  const { blob } = await http.get(path, { responseType: 'blob' });
  return URL.createObjectURL(blob);
}

export const audioService = {
  // POST /api/audio/upload-segment (multipart/form-data)
  uploadSegment: (meetingId, segmentNumber, blob, filename) => {
    const form = new FormData();
    form.append('meeting_id', String(meetingId));
    form.append('segment_number', String(segmentNumber));
    form.append('audio', blob, filename);
    return http.post('/api/audio/upload-segment', form, { isForm: true });
  },

  // POST /api/audio/end-meeting
  endMeeting: (meetingId) => http.post('/api/audio/end-meeting', { meeting_id: meetingId }),

  // GET /api/audio/status/{meeting_id}
  status: (meetingId) => http.get(`/api/audio/status/${meetingId}`),
};
