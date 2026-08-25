import { http } from './httpClient';

export const billingService = {
  plans: () => http.get('/api/billing/plans', { auth: false }),
  current: () => http.get('/api/billing/subscription'),
  payments: () => http.get('/api/billing/payments'),
  quote: (payload) => http.post('/api/billing/quote', payload),
  checkout: (payload) => http.post('/api/billing/checkout', payload),
  payment: (id) => http.get(`/api/billing/payments/${id}`),
};
