// Domaine 6 - Export (2 endpoints)
import { http } from './httpClient';

export const exportService = {
  // GET /api/export/pdf/{id} — reponse binaire, declenche un telechargement
  downloadPdf: async (meetingId, includeTranscript = false) => {
    const query = includeTranscript ? '?include_transcript=true' : '';
    const { blob, filename } = await http.get(`/api/export/pdf/${meetingId}${query}`, { responseType: 'blob' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `compte_rendu_reunion_${meetingId}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  // GET /api/export/json/{id}
  exportJson: (meetingId) => http.get(`/api/export/json/${meetingId}`),

  // POST /api/export/send-report — genere le PDF (s'il ne l'est pas deja) et
  // l'envoie par email a une ou plusieurs adresses via Resend.
  sendReport: (meetingId, emails, subject, html) =>
    http.post('/api/export/send-report', {
      meeting_id: Number(meetingId),
      emails,
      ...(subject ? { subject } : {}),
      ...(html ? { html } : {}),
    }),
};
