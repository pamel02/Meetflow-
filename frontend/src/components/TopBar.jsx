import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useBackendHealth } from '../hooks/useBackendHealth';
import { useLayout } from '../context/LayoutContext';

const HEALTH_LABEL = { checking: 'Vérification…', ok: 'Système opérationnel', degraded: 'Service dégradé', unreachable: 'Backend indisponible' };

export default function TopBar({ title }) {
  const { user, logout } = useAuth();
  const health = useBackendHealth();
  const navigate = useNavigate();
  const { toggleSidebar } = useLayout();
  const initials = (user?.name || 'MF').split(' ').slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  const handleLogout = async () => { await logout(); navigate('/connexion'); };
  const dotTone = health.state === 'ok' ? 'bg-emerald-500' : health.state === 'checking' ? 'bg-amber-400' : 'bg-red-500';

  return (
    <header className="flex h-[72px] shrink-0 items-center justify-between gap-4 border-b border-liseret bg-white px-4 sm:px-6 md:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button onClick={toggleSidebar} aria-label="Ouvrir le menu" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-liseret text-encre-sourde hover:bg-surface-haute md:hidden"><span aria-hidden="true" className="flex flex-col gap-1"><span className="h-px w-4 bg-current"/><span className="h-px w-4 bg-current"/><span className="h-px w-4 bg-current"/></span></button>
        <h1 className="truncate text-lg font-semibold tracking-[-0.02em] text-encre sm:text-xl">{title}</h1>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-full border border-liseret bg-fond px-3 py-2 text-xs font-medium text-encre-sourde sm:flex" title={JSON.stringify(health.components || {})}><span className={`h-2 w-2 rounded-full ${dotTone}`} />{HEALTH_LABEL[health.state]}</div>
        <button aria-label="Notifications" className="hidden h-10 w-10 items-center justify-center rounded-full text-encre-sourde hover:bg-surface-haute sm:flex"><svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg></button>
        <button onClick={handleLogout} title="Se déconnecter" className="flex items-center gap-2 rounded-full border border-liseret bg-white p-1 pr-2.5 shadow-sm hover:border-bordeaux-400"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-bordeaux-500/10 text-xs font-bold text-bordeaux-700">{initials}</span><span className="hidden max-w-28 truncate text-xs font-semibold text-encre md:block">{user?.name || 'Compte'}</span></button>
      </div>
    </header>
  );
}
