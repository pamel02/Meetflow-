import { http } from './httpClient';

export const organizationService = {
  create: (data) => http.post('/api/organizations', data),
  current: () => http.get('/api/organizations/current'),
  members: () => http.get('/api/organizations/members'),
  invite: (email, role) => http.post('/api/organizations/invitations', { email, role }),
  updateRole: (membershipId, role) => http.patch(`/api/organizations/members/${membershipId}`, { role }),
  removeMember: (membershipId) => http.delete(`/api/organizations/members/${membershipId}`),
};
