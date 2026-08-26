import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutProvider } from '../context/LayoutContext';
import { Loader } from './Loader';
import Sidebar from './Sidebar';

export default function ProtectedRoute() {
  const { status, user } = useAuth();
  const location = useLocation();
  if (status === 'checking') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-fond">
        <Loader label="Vérification de la session…" />
      </div>
    );
  }

  if (status === 'anonymous') {
    return <Navigate to="/connexion" state={{ from: `${location.pathname}${location.search}` }} replace />;
  }

  if (user?.onboarding_required) return <Navigate to="/onboarding" replace />;

  return (
    <LayoutProvider>
      <div className="flex h-dvh overflow-hidden bg-fond text-encre">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Outlet />
        </div>
      </div>
    </LayoutProvider>
  );
}
