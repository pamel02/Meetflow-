// Domaine 5 - Assistant IA / Chat RAG (2 endpoints)
import { http } from './httpClient';

export const chatService = {
  // POST /api/chat — question globale sur toutes les reunions
  ask: (question) => http.post('/api/chat', { question }),

  // POST /api/chat/{meeting_id} — question ciblee sur une reunion
  askAbout: (meetingId, question) => http.post(`/api/chat/${meetingId}`, { question }),
};
