import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import ProtectedRoute from './components/ProtectedRoute';
import PublicOnlyRoute from './components/PublicOnlyRoute';
import AuthenticatedRoute from './components/AuthenticatedRoute';
import ErrorBoundary from './ErrorBoundary';

import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import MeetingDetail from './pages/MeetingDetail';
import Assistant from './pages/Assistant';
import History from './pages/History';
import Settings from './pages/Settings';
import Onboarding from './pages/Onboarding';
import Team from './pages/Team';
import Landing from './pages/Landing';
import Billing from './pages/Billing';
import ForgotPassword from './pages/ForgotPassword';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <AuthProvider>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route element={<PublicOnlyRoute />}>
                <Route path="/connexion" element={<Login />} />
                <Route path="/inscription" element={<Register />} />
                <Route path="/verification-email" element={<VerifyEmail />} />
                <Route path="/mot-de-passe-oublie" element={<ForgotPassword />} />
              </Route>

              <Route element={<AuthenticatedRoute />}>
                <Route path="/onboarding" element={<Onboarding />} />
              </Route>

              <Route element={<ProtectedRoute />}>
                <Route path="/app" element={<Dashboard />} />
                <Route path="/reunions/:id" element={<MeetingDetail />} />
                <Route path="/assistant" element={<Assistant />} />
                <Route path="/historique" element={<History />} />
                <Route path="/parametres" element={<Settings />} />
                <Route path="/equipe" element={<Team />} />
                <Route path="/facturation" element={<Billing />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
