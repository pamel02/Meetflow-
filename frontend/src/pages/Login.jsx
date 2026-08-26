import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Link, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Button from '../components/Button';
import Input from '../components/Input';
import PasswordField from '../components/PasswordField';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login, sessionMessage, setSessionMessage } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const invitedEmail = (searchParams.get('email') || '').trim().toLowerCase();
  const invitationOrganization = searchParams.get('entreprise');
  const [email, setEmail] = useState(invitedEmail);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSessionMessage(null);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from || '/app', { replace: true });
    } catch (err) {
      if (err.payload?.code === 'EMAIL_NOT_VERIFIED') {
        navigate('/verification-email', { state: { email: err.payload.email } });
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout mode="login" title="Connectez-vous à MeetFlow" description="Accédez à l’espace sécurisé de votre entreprise.">
      {invitedEmail && <div className="mt-6 rounded-xl border border-bordeaux-400/25 bg-bordeaux-500/5 px-4 py-3 text-sm leading-relaxed text-bordeaux-900"><strong>Invitation {invitationOrganization ? `à rejoindre ${invitationOrganization}` : 'entreprise'} :</strong> connectez-vous avec l’adresse invitée. Votre accès sera rattaché automatiquement.</div>}
      {sessionMessage && <div role="status" className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{sessionMessage}</div>}
      {location.state?.passwordResetMessage && <div role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{location.state.passwordResetMessage}</div>}
      {location.state?.activationMessage && <div role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{location.state.activationMessage}</div>}

      <form onSubmit={handleSubmit} className="mt-7 flex flex-col gap-5 rounded-2xl border border-liseret bg-white p-6 shadow-[0_18px_50px_rgba(16,24,40,0.07)]">
        <Input label="Adresse email professionnelle" type="email" name="email" autoComplete="email" inputMode="email" autoCapitalize="none" spellCheck="false" autoFocus required disabled={loading || Boolean(invitedEmail)} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@entreprise.com" hint={invitedEmail ? 'Cette adresse est liée à votre invitation.' : undefined} />
        <PasswordField label="Mot de passe" name="password" autoComplete="current-password" required disabled={loading} value={password} onChange={(event) => setPassword(event.target.value)} />
        <div className="-mt-2 text-right"><Link to="/mot-de-passe-oublie" className="text-xs font-semibold text-bordeaux-700 hover:text-bordeaux-800">Mot de passe oublié ?</Link></div>

        {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <Button type="submit" size="lg" loading={loading} className="mt-1 w-full">
          {loading ? 'Connexion en cours…' : 'Se connecter'}
        </Button>
      </form>
    </AuthLayout>
  );
}
