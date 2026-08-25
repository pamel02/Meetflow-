import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader } from './Loader';

export default function AuthenticatedRoute() {
  const { status } = useAuth();
  if (status === 'checking') return <div className="flex min-h-dvh items-center justify-center bg-fond"><Loader label="Vérification de la session…" /></div>;
  if (status === 'anonymous') return <Navigate to="/connexion" replace />;
  return <Outlet />;
}
