// Domaine 4 - Donnees IA (7 endpoints)
import { http } from './httpClient';

export const aiDataService = {
  // GET /api/transcript/{id}
  transcript: (id) => http.get(`/api/transcript/${id}`),

  // GET /api/summary/{id}
  summary: (id) => http.get(`/api/summary/${id}`),

  // GET /api/actions/{id}
  actions: (id) => http.get(`/api/actions/${id}`),

  // GET /api/decisions/{id}
  decisions: (id) => http.get(`/api/decisions/${id}`),

  // GET /api/questions/{id}
  questions: (id) => http.get(`/api/questions/${id}`),

  // GET /api/risks/{id}
  risks: (id) => http.get(`/api/risks/${id}`),

  // GET /api/report/{id} — regroupe les 6 endpoints ci-dessus en un seul appel
  report: (id) => http.get(`/api/report/${id}`),
};
