import { useState } from 'react';
import Button from './Button';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Champ permettant de saisir plusieurs adresses email : on tape une adresse
 * puis Entree / virgule / bouton "Ajouter" pour la valider sous forme de
 * jeton retirable. `emails` et `onChange` sont controles par le parent.
 */
export default function EmailChipsField({ label, emails, onChange, disabled = false, placeholder = 'adresse@email.com' }) {
  const [draft, setDraft] = useState('');
  const [error, setError] = useState(null);

  const addEmail = () => {
    const value = draft.trim().replace(/,$/, '');
    if (!value) return;
    if (!EMAIL_RE.test(value)) {
      setError('Adresse email invalide.');
      return;
    }
    if (emails.includes(value)) {
      setDraft('');
      return;
    }
    onChange([...emails, value]);
    setDraft('');
    setError(null);
  };

  const removeEmail = (value) => onChange(emails.filter((e) => e !== value));

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addEmail();
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {label && (
        <span className="text-xs font-semibold text-encre-douce">{label}</span>
      )}
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            if (error) setError(null);
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          className={`min-w-0 flex-1 rounded-xl border bg-white px-3.5 py-2.5 text-sm text-encre shadow-sm placeholder:text-taupe-500 focus:border-bordeaux-500 disabled:opacity-50 ${
            error ? 'border-bordeaux-500' : 'border-liseret'
          }`}
        />
        <Button type="button" variant="secondary" onClick={addEmail} disabled={disabled}>
          Ajouter
        </Button>
      </div>
      {error && <span className="text-xs text-bordeaux-400">{error}</span>}
      {emails.length > 0 && (
        <ul className="flex flex-wrap gap-2 pt-1">
          {emails.map((email) => (
            <li
              key={email}
              className="flex items-center gap-2 rounded-full border border-bordeaux-400/40 bg-bordeaux-500/5 px-3 py-1 text-xs font-medium text-bordeaux-700"
            >
              {email}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeEmail(email)}
                  aria-label={`Retirer ${email}`}
                  className="text-encre-sourde hover:text-encre"
                >
                  ×
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
