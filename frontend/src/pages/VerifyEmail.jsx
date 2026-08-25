import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Button from '../components/Button';
import Input from '../components/Input';
import { useAuth } from '../context/AuthContext';

const DEFAULT_COOLDOWN = 60;

export default function VerifyEmail() {
  const { verifyEmail, resendVerification } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState(location.state?.email || '');
  const [code, setCode] = useState('');
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(
    location.state?.emailSent === false
      ? "L'envoi initial a échoué. Vérifiez la configuration email puis demandez un nouveau code."
      : 'Nous avons envoyé un code à 6 chiffres à votre adresse email.'
  );
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(location.state?.resendAfter ?? DEFAULT_COOLDOWN);

  useEffect(() => {
    if (countdown <= 0) return undefined;
    const timer = window.setInterval(() => setCountdown((value) => Math.max(value - 1, 0)), 1000);
    return () => window.clearInterval(timer);
  }, [countdown]);

  const maskedEmail = useMemo(() => maskEmail(email), [email]);

  const handleCodeChange = (event) => {
    setCode(event.target.value.replace(/\D/g, '').slice(0, 6));
    setError(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (code.length !== 6) {
      setError('Saisissez les 6 chiffres du code reçu.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const verifiedUser = await verifyEmail(email.trim(), code);
      navigate(verifiedUser?.onboarding_required ? '/onboarding' : '/app', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email.trim() || countdown > 0) return;
    setResending(true);
    setError(null);
    try {
      const data = await resendVerification(email.trim());
      setNotice(data.message || 'Un nouveau code a été envoyé.');
      setCountdown(data.resend_after ?? DEFAULT_COOLDOWN);
      setCode('');
    } catch (err) {
      if (err.payload?.retry_after) setCountdown(err.payload.retry_after);
      setError(err.message);
    } finally {
      setResending(false);
    }
  };

  return (
    <AuthLayout mode="register" title="Vérifiez votre email" description="Cette étape protège votre espace entreprise contre les inscriptions non autorisées.">
      <form onSubmit={handleSubmit} className="mt-7 flex flex-col gap-5 rounded-2xl border border-liseret bg-white p-6 shadow-[0_18px_50px_rgba(16,24,40,0.07)]">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-bordeaux-500/10 text-bordeaux-700">
          <MailIcon />
        </div>

        {email ? (
          <div>
            <p className="text-sm leading-relaxed text-encre-sourde">Code envoyé à</p>
            <p className="mt-1 font-semibold text-encre">{maskedEmail}</p>
          </div>
        ) : (
          <Input label="Adresse email" type="email" name="verification-email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@entreprise.com" />
        )}

        <div className="flex flex-col gap-2">
          <label htmlFor="verification-code" className="text-xs font-semibold text-encre-douce">Code de vérification</label>
          <input
            id="verification-code"
            name="verification-code"
            type="text"
            inputMode="numeric"
            pattern="[0-9]{6}"
            autoComplete="one-time-code"
            autoFocus={Boolean(email)}
            required
            maxLength={6}
            disabled={loading}
            value={code}
            onChange={handleCodeChange}
            placeholder="000000"
            aria-invalid={Boolean(error)}
            className={`w-full rounded-xl border bg-white px-4 py-3.5 text-center font-donnees text-2xl font-semibold tracking-[0.45em] text-encre shadow-sm transition placeholder:text-taupe-300 focus:border-bordeaux-500 focus:ring-3 focus:ring-bordeaux-500/10 ${error ? 'border-red-300' : 'border-liseret'}`}
          />
          <p className="text-xs text-encre-sourde">Le code reste valable pendant 10 minutes.</p>
        </div>

        {notice && <p role="status" className="rounded-xl border border-bordeaux-400/25 bg-bordeaux-500/5 px-3 py-2 text-sm leading-relaxed text-bordeaux-900">{notice}</p>}
        {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <Button type="submit" size="lg" loading={loading} disabled={!email || code.length !== 6} className="w-full">
          {loading ? 'Vérification en cours…' : 'Vérifier et continuer'}
        </Button>

        <div className="text-center text-sm text-encre-sourde">
          Vous n’avez rien reçu ?{' '}
          <button type="button" onClick={handleResend} disabled={!email || countdown > 0 || resending} className="font-semibold text-bordeaux-700 transition hover:text-bordeaux-900 disabled:cursor-not-allowed disabled:text-taupe-500">
            {resending ? 'Envoi…' : countdown > 0 ? `Renvoyer dans ${countdown}s` : 'Renvoyer le code'}
          </button>
        </div>
      </form>

      <p className="mt-5 text-center text-sm text-encre-sourde">
        Mauvaise adresse ? <Link to="/inscription" className="font-semibold text-bordeaux-700 hover:text-bordeaux-900">Recommencer l’inscription</Link>
      </p>
    </AuthLayout>
  );
}

function maskEmail(email) {
  const [local, domain] = email.split('@');
  if (!local || !domain) return email;
  const visible = local.slice(0, Math.min(2, local.length));
  return `${visible}${'•'.repeat(Math.max(local.length - visible.length, 2))}@${domain}`;
}

function MailIcon() {
  return <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></svg>;
}
