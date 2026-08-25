import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Button from '../components/Button';
import Input from '../components/Input';
import { useAuth } from '../context/AuthContext';
import { organizationService } from '../services';

export default function Onboarding() {
  const { user, refreshProfile, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({ name: '', sector: '', company_size: '', country: 'Cameroun' });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true); setError(null);
    try {
      await organizationService.create(form);
      await refreshProfile();
      const plan = searchParams.get('plan') || sessionStorage.getItem('meetflow_selected_plan');
      sessionStorage.setItem('meetflow_activation_pending', 'true');
      if (['starter', 'business', 'enterprise'].includes(plan)) {
        sessionStorage.setItem('meetflow_selected_plan', plan);
        navigate(`/facturation?plan=${plan}`, { replace: true, state: { activationRequired: true } });
      } else {
        navigate('/facturation', { replace: true, state: { activationRequired: true, subscriptionRequired: true } });
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-dvh bg-fond px-5 py-8 sm:px-8">
      <header className="mx-auto flex max-w-5xl items-center justify-between">
        <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-bordeaux-700 font-bold text-white">M</span><div><p className="font-bold text-encre">MeetFlow</p><p className="text-xs text-encre-sourde">Configuration de l’espace</p></div></div>
        <button onClick={() => logout()} className="text-sm font-medium text-encre-sourde hover:text-encre">Se déconnecter</button>
      </header>
      <main className="mx-auto mt-12 grid max-w-5xl overflow-hidden rounded-3xl border border-liseret bg-white shadow-[0_24px_70px_rgba(16,24,40,0.08)] lg:grid-cols-[0.82fr_1.18fr]">
        <aside className="bg-bordeaux-950 p-8 text-white sm:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-bordeaux-400">Étape 2 sur 3</p>
          <h1 className="mt-4 text-3xl font-bold tracking-[-0.04em]">Créez votre espace entreprise</h1>
          <p className="mt-4 text-sm leading-relaxed text-white/65">Bonjour {user?.name}. Cet espace isolera vos réunions et accueillera les membres de votre équipe.</p>
          <div className="mt-10 space-y-5"><Step number="1" title="Compte vérifié" done /><Step number="2" title="Entreprise et équipe" active /><Step number="3" title="Activation de l’abonnement" /></div>
        </aside>
        <form onSubmit={submit} className="p-7 sm:p-10">
          <h2 className="text-xl font-bold text-encre">Informations de l’entreprise</h2>
          <p className="mt-2 text-sm text-encre-sourde">Vous pourrez modifier ces informations ultérieurement.</p>
          <div className="mt-7 grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2"><Input label="Nom de l’entreprise" name="organization-name" required minLength={2} maxLength={160} autoFocus value={form.name} onChange={update('name')} placeholder="Ex. Nova Consulting" /></div>
            <Input label="Secteur d’activité" value={form.sector} onChange={update('sector')} placeholder="Conseil, technologie…" />
            <label className="flex flex-col gap-2"><span className="text-xs font-semibold text-encre-douce">Taille de l’entreprise</span><select required value={form.company_size} onChange={update('company_size')} className="rounded-xl border border-liseret bg-white px-3.5 py-3 text-sm text-encre shadow-sm"><option value="">Sélectionner</option><option value="1-10">1 à 10</option><option value="11-50">11 à 50</option><option value="51-200">51 à 200</option><option value="201+">Plus de 200</option></select></label>
            <div className="sm:col-span-2"><Input label="Pays" value={form.country} onChange={update('country')} /></div>
          </div>
          {error && <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
          <Button type="submit" size="lg" loading={loading} className="mt-7 w-full">Créer mon espace</Button>
          <p className="mt-4 text-center text-xs text-encre-sourde">Vous deviendrez administrateur de cet espace.</p>
        </form>
      </main>
    </div>
  );
}

function Step({ number, title, done, active }) {
  return <div className="flex items-center gap-3"><span className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${done ? 'bg-emerald-400 text-emerald-950' : active ? 'bg-white text-bordeaux-800' : 'bg-white/10'}`}>{done ? '✓' : number}</span><span className="text-sm font-medium">{title}</span></div>;
}
