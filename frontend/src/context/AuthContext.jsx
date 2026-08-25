import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  authService,
  saveToken,
  getToken,
  getTokenExpiry,
  clearToken,
  registerUnauthorizedHandler,
} from '../services';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('checking'); // checking | authenticated | anonymous
  const [sessionMessage, setSessionMessage] = useState(null);

  const logout = useCallback(async (silent = false) => {
    if (!silent) {
      try {
        await authService.logout();
      } catch {
        // Le token est peut-etre deja expire : on nettoie quand meme localement.
      }
    }
    clearToken();
    setUser(null);
    setStatus('anonymous');
  }, []);

  // Deconnexion automatique quand le token expire (session de 12h).
  useEffect(() => {
    const expiry = getTokenExpiry();
    if (!expiry || status !== 'authenticated') return undefined;
    const msLeft = new Date(expiry).getTime() - Date.now();
    if (msLeft <= 0) {
      setSessionMessage('Votre session a expiré. Veuillez vous reconnecter.');
      logout(true);
      return undefined;
    }
    const timer = setTimeout(() => {
      setSessionMessage('Votre session a expiré. Veuillez vous reconnecter.');
      logout(true);
    }, msLeft);
    return () => clearTimeout(timer);
  }, [status, logout]);

  useEffect(() => {
    registerUnauthorizedHandler(() => {
      setSessionMessage('Votre session a expiré. Veuillez vous reconnecter.');
      clearToken();
      setUser(null);
      setStatus('anonymous');
    });
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      const token = getToken();
      if (!token) {
        setStatus('anonymous');
        return;
      }
      try {
        const data = await authService.me();
        setUser(data.user);
        setStatus('authenticated');
      } catch {
        clearToken();
        setStatus('anonymous');
      }
    };
    bootstrap();
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authService.login(email, password);
    saveToken(data.access_token, data.expires_at);
    setUser(data.user);
    setStatus('authenticated');
    setSessionMessage(null);
    return data.user;
  }, []);

  const register = useCallback(async (name, email, password) => {
    return authService.register(name, email, password);
  }, []);

  const verifyEmail = useCallback(async (email, code) => {
    const data = await authService.verifyEmail(email, code);
    saveToken(data.access_token, data.expires_at);
    setUser(data.user);
    setStatus('authenticated');
    setSessionMessage(null);
    return data.user;
  }, []);

  const resendVerification = useCallback(
    (email) => authService.resendVerification(email),
    []
  );

  const refreshProfile = useCallback(async () => {
    const data = await authService.me();
    setUser(data.user);
    return data.user;
  }, []);

  const value = useMemo(
    () => ({ user, status, sessionMessage, setSessionMessage, login, register, verifyEmail, resendVerification, logout, refreshProfile }),
    [user, status, sessionMessage, login, register, verifyEmail, resendVerification, logout, refreshProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé à l\'intérieur de AuthProvider');
  return ctx;
}
