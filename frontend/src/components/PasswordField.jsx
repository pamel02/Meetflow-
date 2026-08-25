import { useState } from 'react';

export default function PasswordField({ label, hint, error, id, name, disabled = false, ...rest }) {
  const [visible, setVisible] = useState(false);
  const inputId = id || name;
  const descriptionId = error || hint ? `${inputId}-description` : undefined;

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={inputId} className="text-xs font-semibold text-encre-douce">{label}</label>
      <div className="relative">
        <input
          {...rest}
          id={inputId}
          name={name}
          disabled={disabled}
          type={visible ? 'text' : 'password'}
          aria-invalid={Boolean(error)}
          aria-describedby={descriptionId}
          className={`w-full rounded-xl border bg-white px-3.5 py-3 pr-12 text-sm text-encre shadow-sm transition placeholder:text-taupe-500 focus:border-bordeaux-500 focus:ring-3 focus:ring-bordeaux-500/10 ${error ? 'border-red-300' : 'border-liseret'}`}
        />
        <button type="button" disabled={disabled} onClick={() => setVisible((current) => !current)} className="absolute inset-y-0 right-1 flex w-10 items-center justify-center rounded-lg text-encre-sourde transition hover:bg-surface-haute hover:text-encre disabled:cursor-not-allowed disabled:opacity-50" aria-label={visible ? 'Masquer le mot de passe' : 'Afficher le mot de passe'} aria-pressed={visible}>
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
      {(error || hint) && <span id={descriptionId} className={`text-xs ${error ? 'text-red-600' : 'text-encre-sourde'}`}>{error || hint}</span>}
    </div>
  );
}

function EyeIcon() {
  return <svg viewBox="0 0 24 24" className="h-4.5 w-4.5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></svg>;
}

function EyeOffIcon() {
  return <svg viewBox="0 0 24 24" className="h-4.5 w-4.5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="m3 3 18 18" /><path d="M10.6 6.1A10.7 10.7 0 0 1 12 6c6 0 9.5 6 9.5 6a15 15 0 0 1-2.1 2.8M6.4 6.4C3.9 8.2 2.5 12 2.5 12s3.5 6 9.5 6a9.8 9.8 0 0 0 3.1-.5" /><path d="M10.2 10.2a2.5 2.5 0 0 0 3.6 3.6" /></svg>;
}

export function PasswordStrength({ password }) {
  const checks = [password.length >= 8, password.length >= 12, /[a-zA-Z]/.test(password) && /\d/.test(password), /[^a-zA-Z0-9]/.test(password)];
  const score = checks.filter(Boolean).length;
  const labels = ['À compléter', 'Faible', 'Correct', 'Bon', 'Excellent'];

  return (
    <div aria-live="polite">
      <div className="grid grid-cols-4 gap-1.5" aria-hidden="true">
        {[1, 2, 3, 4].map((level) => <span key={level} className={`h-1 rounded-full ${score >= level ? 'bg-bordeaux-600' : 'bg-surface-haute'}`} />)}
      </div>
      <div className="mt-2 flex items-center justify-between gap-3 text-xs">
        <span className={password.length >= 8 ? 'text-emerald-700' : 'text-encre-sourde'}>{password.length >= 8 ? '✓ 8 caractères minimum' : '8 caractères minimum'}</span>
        {password && <span className="font-medium text-encre-sourde">{labels[score]}</span>}
      </div>
    </div>
  );
}
