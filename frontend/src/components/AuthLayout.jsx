import { Link } from 'react-router-dom';

const CONTENT = {
  login: {
    eyebrow: 'Intelligence de réunion',
    title: 'Chaque échange devient une décision claire.',
    description: 'Retrouvez les comptes rendus, les décisions et les actions de votre entreprise dans un espace unique.',
  },
  register: {
    eyebrow: 'Espace entreprise',
    title: 'Construisez une mémoire qui fait avancer vos équipes.',
    description: 'Centralisez les discussions, les responsabilités et le suivi sans alourdir le quotidien de vos collaborateurs.',
  },
  reset: {
    eyebrow: 'Accès sécurisé',
    title: 'Récupérez votre compte en toute sécurité.',
    description: 'Un code temporaire envoyé par email vous permet de définir un nouveau mot de passe sans exposer vos données.',
  },
};

export default function AuthLayout({ mode, title, description, children }) {
  const content = CONTENT[mode];

  return (
    <div className="grid min-h-dvh bg-white lg:grid-cols-[1.05fr_0.95fr]">
      <aside className="relative hidden min-h-dvh overflow-hidden bg-bordeaux-950 px-10 py-9 text-white lg:flex lg:flex-col lg:justify-between xl:px-14 xl:py-11">
        <div className="absolute -left-32 top-1/3 h-96 w-96 rounded-full bg-bordeaux-500/30 blur-3xl" />
        <div className="absolute -right-24 bottom-0 h-80 w-80 rounded-full bg-bordeaux-400/20 blur-3xl" />
        <Brand inverse />
        <div className="relative max-w-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-bordeaux-400">{content.eyebrow}</p>
          <h2 className="mt-5 text-4xl font-bold leading-[1.08] tracking-[-0.05em] xl:text-5xl">{content.title}</h2>
          <p className="mt-6 max-w-lg text-base leading-relaxed text-white/65">{content.description}</p>
          <div className="mt-9 grid max-w-lg gap-3 sm:grid-cols-3">
            <Benefit title="Centralisé" label="Réunions et actions" />
            <Benefit title="Structuré" label="Comptes rendus" />
            <Benefit title="Sécurisé" label="Session entreprise" />
          </div>
        </div>
        <p className="relative text-xs text-white/40">MeetFlow AI · Pensé pour les équipes qui avancent</p>
      </aside>

      <main className="flex min-w-0 items-center justify-center bg-fond px-5 py-8 sm:px-10 lg:py-12">
        <div className="w-full min-w-0 max-w-md">
          <div className="mb-8 lg:hidden"><Brand /></div>
          <nav className="mb-8 grid grid-cols-2 rounded-xl border border-liseret bg-surface-haute p-1" aria-label="Authentification">
            <AuthTab to="/connexion" active={mode === 'login'}>Connexion</AuthTab>
            <AuthTab to="/inscription" active={mode === 'register'}>Créer un compte</AuthTab>
          </nav>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">
            {mode === 'login' ? 'Bienvenue' : mode === 'reset' ? 'Récupération du compte' : 'Nouvel espace'}
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-encre sm:text-3xl">{title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-encre-sourde">{description}</p>
          {children}
          <div className="mt-6 flex items-start gap-2.5 rounded-xl border border-liseret bg-white/70 px-4 py-3 text-xs leading-relaxed text-encre-sourde">
            <ShieldIcon />
            <p>Votre session reste limitée à cet onglet de navigation et expire automatiquement.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function AuthTab({ to, active, children }) {
  return (
    <Link to={to} aria-current={active ? 'page' : undefined} className={`rounded-lg px-3 py-2.5 text-center text-sm font-semibold transition ${active ? 'bg-white text-bordeaux-700 shadow-sm' : 'text-encre-sourde hover:text-encre'}`}>
      {children}
    </Link>
  );
}

function Brand({ inverse = false }) {
  return (
    <div className="relative flex items-center gap-3">
      <span className={`flex h-10 w-10 items-center justify-center rounded-xl text-sm font-extrabold ${inverse ? 'bg-white text-bordeaux-700' : 'bg-bordeaux-700 text-white'}`}>M</span>
      <div>
        <p className={inverse ? 'font-bold text-white' : 'font-bold text-encre'}>MeetFlow</p>
        <p className={inverse ? 'text-xs text-white/55' : 'text-xs text-encre-sourde'}>Intelligence</p>
      </div>
    </div>
  );
}

function Benefit({ title, label }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
      <div className="mb-3 flex h-6 w-6 items-center justify-center rounded-full bg-white/10"><CheckIcon /></div>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 text-xs text-white/50">{label}</p>
    </div>
  );
}

function CheckIcon() {
  return <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true"><path d="m5 10 3 3 7-7" /></svg>;
}

function ShieldIcon() {
  return <svg viewBox="0 0 24 24" className="mt-0.5 h-4 w-4 shrink-0 text-bordeaux-600" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M12 3 5 6v5c0 4.7 2.8 8.2 7 10 4.2-1.8 7-5.3 7-10V6l-7-3Z" /><path d="m9 12 2 2 4-4" /></svg>;
}
