import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Button from '../components/Button';
import Input from '../components/Input';
import PasswordField, { PasswordStrength } from '../components/PasswordField';
import { authService } from '../services';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const requestCode = async (event) => {
    event.preventDefault(); setLoading(true); setError(null);
    try {
      const data = await authService.requestPasswordReset(email.trim());
      setMessage(data.message); setStep('reset');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const submitReset = async (event) => {
    event.preventDefault(); setError(null);
    if (password !== confirmation) { setError('Les deux mots de passe ne correspondent pas.'); return; }
    setLoading(true);
    try {
      const data = await authService.resetPassword(email.trim(), code, password);
      navigate('/connexion', { replace: true, state: { passwordResetMessage: data.message } });
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return <AuthLayout mode="reset" title={step === 'email' ? 'Mot de passe oublié' : 'Choisissez un nouveau mot de passe'} description={step === 'email' ? 'Indiquez l’adresse email associée à votre compte.' : `Saisissez le code à 6 chiffres envoyé à ${email}.`}>
    {message && <p className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</p>}
    {step === 'email' ? <form onSubmit={requestCode} className="mt-7 flex flex-col gap-5 rounded-2xl border border-liseret bg-white p-6 shadow-[0_18px_50px_rgba(16,24,40,0.07)]"><Input label="Adresse email professionnelle" type="email" autoComplete="email" autoFocus required disabled={loading} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@entreprise.com" />{error && <ErrorMessage>{error}</ErrorMessage>}<Button type="submit" size="lg" loading={loading}>Recevoir mon code</Button></form> : <form onSubmit={submitReset} className="mt-7 flex flex-col gap-5 rounded-2xl border border-liseret bg-white p-6 shadow-[0_18px_50px_rgba(16,24,40,0.07)]"><Input label="Code de réinitialisation" inputMode="numeric" autoComplete="one-time-code" required minLength={6} maxLength={6} value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" /><PasswordField label="Nouveau mot de passe" autoComplete="new-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} /><PasswordStrength password={password} /><PasswordField label="Confirmer le mot de passe" autoComplete="new-password" required minLength={8} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />{error && <ErrorMessage>{error}</ErrorMessage>}<Button type="submit" size="lg" loading={loading} disabled={code.length !== 6 || password.length < 8}>Réinitialiser mon mot de passe</Button><button type="button" onClick={() => { setStep('email'); setMessage(null); setCode(''); }} className="text-sm font-semibold text-encre-sourde hover:text-bordeaux-700">Utiliser une autre adresse</button></form>}
    <p className="mt-6 text-center text-sm text-encre-sourde"><Link to="/connexion" className="font-semibold text-bordeaux-700">Retour à la connexion</Link></p>
  </AuthLayout>;
}

function ErrorMessage({ children }) { return <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{children}</p>; }
