// Domaine 7 - Monitoring et diagnostic (2 endpoints)
import { http } from './httpClient';

export const monitoringService = {
  // GET /api/health
  health: () => http.get('/api/health', { auth: false }),

  // GET /api/models
  models: () => http.get('/api/models', { auth: false }),
};
