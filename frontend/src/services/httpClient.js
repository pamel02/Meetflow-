// Client HTTP bas niveau : ajoute le header Authorization, gere le JSON et
// normalise les erreurs pour que les services au-dessus restent simples.

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const TOKEN_KEY = 'reunion_ia_token';
const TOKEN_EXPIRY_KEY = 'reunion_ia_token_expiry';

export function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (!API_BASE_URL) return normalizedPath;

  if (/^https?:\/\//i.test(normalizedPath)) return normalizedPath;

  const normalizedBase = API_BASE_URL.replace(/\/$/, '');
  if (normalizedPath.startsWith(normalizedBase)) return normalizedPath;

  return `${normalizedBase}${normalizedPath}`;
}

export function saveToken(accessToken, expiresAt) {
  sessionStorage.setItem(TOKEN_KEY, accessToken);
  if (expiresAt) sessionStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt);
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getTokenExpiry() {
  return sessionStorage.getItem(TOKEN_EXPIRY_KEY);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_EXPIRY_KEY);
}

export function isTokenExpired() {
  const expiry = getTokenExpiry();
  if (!expiry) return false;
  return new Date(expiry).getTime() <= Date.now();
}

/** Erreur normalisee, toujours porteuse d'un message francais et du code HTTP. */
export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

function extractMessage(payload, fallback) {
  if (!payload) return fallback;
  if (Array.isArray(payload.errors) && payload.errors.length) return payload.errors.join(' ');
  if (payload.error) return payload.error;
  if (payload.message) return payload.message;
  return fallback;
}

let onUnauthorized = null;
export function registerUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

/**
 * Effectue une requete vers l'API.
 * @param {string} path chemin relatif, ex: "/api/meetings"
 * @param {object} options { method, body, isForm, auth, responseType }
 */
export async function request(path, options = {}) {
  const { method = 'GET', body, isForm = false, auth = true, responseType = 'json' } = options;

  const headers = {};
  if (!isForm) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let fetchBody;
  if (isForm) fetchBody = body;
  else if (body !== undefined) fetchBody = JSON.stringify(body);

  let response;
  try {
    response = await fetch(buildApiUrl(path), { method, headers, body: fetchBody });
  } catch {
    throw new ApiError(
      "Impossible de joindre le serveur. Verifiez que le backend est demarre.",
      0,
      null
    );
  }

  if (response.status === 401 && auth) {
    if (onUnauthorized) onUnauthorized();
  }

  if (response.status === 202) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(extractMessage(payload, 'Traitement en cours.'), 202, payload);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(extractMessage(payload, `Erreur ${response.status}`), response.status, payload);
  }

  if (responseType === 'blob') {
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    return { blob, filename: match ? match[1] : null };
  }

  if (response.status === 204) return null;
  return response.json().catch(() => null);
}

export const http = {
  get: (path, opts) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  put: (path, body, opts) => request(path, { ...opts, method: 'PUT', body }),
  patch: (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, body, opts) => request(path, { ...opts, method: 'DELETE', body }),
};
