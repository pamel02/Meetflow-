import { NavLink, useNavigate } from 'react-router-dom';
import { useLayout } from '../context/LayoutContext';
import { useAuth } from '../context/AuthContext';

const LINKS = [
  { to: '/facturation', label: 'Facturation', icon: 'billing' },
  { to: '/app', label: 'Vue d’ensemble', icon: 'overview', end: true },
  { to: '/assistant', label: 'Assistant IA', icon: 'sparkles' },
  { to: '/historique', label: 'Réunions', icon: 'calendar' },
  { to: '/equipe', label: 'Équipe', icon: 'team' },
  { to: '/parametres', label: 'Paramètres', icon: 'settings' },
];

function NavIcon({ name }) {
  const paths = {
    billing: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h3"/></>,
    overview: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    sparkles: <><path d="m12 3 1.25 3.75L17 8l-3.75 1.25L12 13l-1.25-3.75L7 8l3.75-1.25L12 3Z"/><path d="m5 14 .9 2.1L8 17l-2.1.9L5 20l-.9-2.1L2 17l2.1-.9L5 14Z"/><path d="m19 13 .9 2.1L22 16l-2.1.9L19 19l-.9-2.1L16 16l2.1-.9L19 13Z"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
    team: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.09A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.09A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.09A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.16.36.36.7.6 1 .28.3.66.48 1.1.4H21v4h-.09A1.7 1.7 0 0 0 19.4 15Z"/></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export default function Sidebar() {
  const { sidebarOpen, closeSidebar } = useLayout();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const handleLogout = async () => {
    closeSidebar();
    await logout();
    navigate('/connexion', { replace: true });
  };
  return (
    <>
      <div onClick={closeSidebar} aria-hidden="true" className={`fixed inset-0 z-40 bg-encre/35 backdrop-blur-sm transition-opacity duration-200 md:hidden ${sidebarOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`} />
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[272px] shrink-0 flex-col border-r border-liseret bg-white transition-transform duration-200 ease-out md:static md:z-auto md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-[88px] items-center justify-between gap-3 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-bordeaux-700 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(38,59,216,0.22)]">M</div>
            <div><p className="text-[17px] font-bold leading-tight tracking-[-0.02em] text-encre">MeetFlow</p><p className="mt-0.5 text-xs font-medium text-encre-sourde">Intelligence</p></div>
          </div>
          <button onClick={closeSidebar} aria-label="Fermer le menu" className="rounded-lg p-2 text-encre-sourde hover:bg-surface-haute hover:text-encre md:hidden">×</button>
        </div>
        {['admin', 'organizer'].includes(user?.organization_role) && <div className="px-4 pb-5 pt-3">
          <NavLink to="/app?nouvelle=1" onClick={closeSidebar} className="flex w-full items-center justify-center gap-2 rounded-xl bg-bordeaux-700 px-4 py-3 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(38,59,216,0.18)] transition hover:bg-bordeaux-800"><span className="text-lg leading-none">+</span>Nouvelle réunion</NavLink>
        </div>}
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3">
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} onClick={closeSidebar} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition-colors ${isActive ? 'bg-bordeaux-500/8 text-bordeaux-700' : 'text-encre-sourde hover:bg-surface-haute hover:text-encre'}`}>
              <NavIcon name={link.icon} />{link.label}
            </NavLink>
          ))}
        </nav>
        <div className="m-4 overflow-hidden rounded-xl border border-liseret bg-fond">
          <div className="px-4 py-3.5"><p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-encre-sourde">Espace entreprise</p><p className="mt-1 truncate text-sm font-semibold text-encre">{user?.organization?.name || 'MeetFlow'}</p><p className="mt-1 truncate text-xs text-encre-sourde">{user?.email}</p></div>
          <button type="button" onClick={handleLogout} className="flex w-full items-center gap-2 border-t border-liseret px-4 py-3 text-left text-sm font-semibold text-encre-sourde transition hover:bg-red-50 hover:text-red-700">
            <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M10 17l5-5-5-5M15 12H3"/><path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5"/></svg>
            Se déconnecter
          </button>
        </div>
      </aside>
    </>
  );
}
