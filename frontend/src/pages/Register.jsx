import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Button from '../components/Button';
import Input from '../components/Input';
import PasswordField, { PasswordStrength } from '../components/PasswordField';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const passwordMismatch = confirmation.length > 0 && password !== confirmation;

  useEffect(() => {
    const plan = searchParams.get('plan');
    if (['starter', 'business', 'enterprise'].includes(plan)) {
      sessionStorage.setItem('meetflow_selected_plan', plan);
    }
  }, [searchParams]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    if (password !== confirmation) {
      setError('Les deux mots de passe ne correspondent pas.');
      return;
    }

    setLoading(true);
    try {
      const data = await register(name.trim(), email.trim(), password);
      navigate('/verification-email', {
        replace: true,
        state: {
          email: email.trim(),
          emailSent: data.email_sent,
          resendAfter: data.resend_after,
        },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout mode="register" title="Créez votre compte" description="Configurez votre accès personnel à MeetFlow en quelques instants.">
      <form onSubmit={handleSubmit} className="mt-7 flex flex-col gap-5 rounded-2xl border border-liseret bg-white p-6 shadow-[0_18px_50px_rgba(16,24,40,0.07)]">
        <Input label="Nom complet" name="name" autoComplete="name" autoFocus required minLength={2} maxLength={120} disabled={loading} value={name} onChange={(event) => setName(event.target.value)} placeholder="Prénom et nom" />
        <Input label="Adresse email professionnelle" type="email" name="email" autoComplete="email" inputMode="email" autoCapitalize="none" spellCheck="false" required disabled={loading} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@entreprise.com" />
        <div className="flex flex-col gap-3">
          <PasswordField label="Mot de passe" name="password" autoComplete="new-password" required minLength={8} disabled={loading} value={password} onChange={(event) => setPassword(event.target.value)} />
          <PasswordStrength password={password} />
        </div>
        <PasswordField label="Confirmer le mot de passe" name="password-confirmation" autoComplete="new-password" required minLength={8} disabled={loading} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} error={passwordMismatch ? 'Les mots de passe ne correspondent pas.' : undefined} />

        {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <Button type="submit" size="lg" loading={loading} disabled={passwordMismatch} className="mt-1 w-full">
          {loading ? 'Création en cours…' : 'Créer mon compte'}
        </Button>
      </form>
    </AuthLayout>
  );
}
