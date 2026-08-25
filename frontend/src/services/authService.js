// Domaine 1 - Authentification (8 endpoints)
import { http } from './httpClient';

export const authService = {
  // POST /api/auth/register
  register: (name, email, password) =>
    http.post('/api/auth/register', { name, email, password }, { auth: false }),

  // POST /api/auth/login
  login: (email, password) =>
    http.post('/api/auth/login', { email, password }, { auth: false }),

  requestPasswordReset: (email) =>
    http.post('/api/auth/forgot-password', { email }, { auth: false }),

  resetPassword: (email, code, newPassword) =>
    http.post('/api/auth/reset-password', { email, code, new_password: newPassword }, { auth: false }),

  // POST /api/auth/verify-email
  verifyEmail: (email, code) =>
    http.post('/api/auth/verify-email', { email, code }, { auth: false }),

  // POST /api/auth/resend-verification
  resendVerification: (email) =>
    http.post('/api/auth/resend-verification', { email }, { auth: false }),

  // GET /api/auth/me
  me: () => http.get('/api/auth/me'),

  // POST /api/auth/refresh
  refresh: () => http.post('/api/auth/refresh'),

  // POST /api/auth/logout
  logout: () => http.post('/api/auth/logout'),

  // PUT /api/auth/profile
  updateProfile: (fields) => http.put('/api/auth/profile', fields),

  // PUT /api/auth/password
  updatePassword: (oldPassword, newPassword) =>
    http.put('/api/auth/password', { old_password: oldPassword, new_password: newPassword }),

  // DELETE /api/auth/account
  deleteAccount: (password) => http.delete('/api/auth/account', { password }),
};
