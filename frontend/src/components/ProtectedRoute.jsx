import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { billingService } from '../services';
import { LayoutProvider } from '../context/LayoutContext';
import { Loader } from './Loader';
import Sidebar from './Sidebar';

export default function ProtectedRoute() {
  const { status, user } = useAuth();
  const location = useLocation();
  const [billingState, setBillingState] = useState({ loading: true, active: false, quotaExhausted: false });

  useEffect(() => {
    if (status !== 'authenticated' || user?.onboarding_required || location.pathname === '/facturation') {
      setBillingState({ loading: false, active: false, quotaExhausted: false });
      return;
    }
    let cancelled = false;
    setBillingState((current) => ({ ...current, loading: true }));
    billingService.current()
      .then((data) => {
        if (!cancelled) setBillingState({
          loading: false,
          active: data.subscription?.status === 'ACTIVE',
          quotaExhausted: Boolean(data.usage?.transcription_quota_exhausted),
        });
      })
      .catch(() => {
        if (!cancelled) setBillingState({ loading: false, active: false, quotaExhausted: false });
      });
    return () => { cancelled = true; };
  }, [status, user?.onboarding_required, location.pathname]);

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

  if (location.pathname !== '/facturation' && billingState.loading) {
    return <div className="flex min-h-screen items-center justify-center bg-fond"><Loader label="Vérification de l’abonnement…" /></div>;
  }

  if (location.pathname !== '/facturation' && (!billingState.active || billingState.quotaExhausted)) {
    if (!billingState.active) sessionStorage.setItem('meetflow_activation_pending', 'true');
    return <Navigate to="/facturation" state={{
      subscriptionRequired: !billingState.active,
      activationRequired: !billingState.active,
      quotaExhausted: billingState.quotaExhausted,
      from: location.pathname,
    }} replace />;
  }

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
