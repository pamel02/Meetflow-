// Domaine 2 - Gestion des reunions (8 endpoints, dont /api/stats et /api/reprocess)
import { http } from './httpClient';

export const meetingService = {
  // POST /api/meetings
  create: (title, description) => http.post('/api/meetings', { title, description }),

  // GET /api/meetings?status=&search=&sort_by=&sort_dir=
  list: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.set('status', params.status);
    if (params.search) query.set('search', params.search);
    if (params.sortBy) query.set('sort_by', params.sortBy);
    if (params.sortDir) query.set('sort_dir', params.sortDir);
    const qs = query.toString();
    return http.get(`/api/meetings${qs ? `?${qs}` : ''}`);
  },

  // GET /api/meetings/{id}
  get: (id) => http.get(`/api/meetings/${id}`),

  // PUT /api/meetings/{id}
  update: (id, fields) => http.put(`/api/meetings/${id}`, fields),

  // DELETE /api/meetings/{id}
  remove: (id) => http.delete(`/api/meetings/${id}`),

  // GET /api/meetings/{id}/status  (polling pipeline)
  status: (id) => http.get(`/api/meetings/${id}/status`),

  // GET /api/stats
  stats: () => http.get('/api/stats'),

  // POST /api/reprocess/{id}
  reprocess: (id) => http.post(`/api/reprocess/${id}`),
};
