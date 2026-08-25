import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { billingService } from '../services';

const FEATURES = [
  { icon: 'mic', title: 'Capturez sans interrompre', text: 'Enregistrez vos réunions et laissez MeetFlow structurer les échanges pendant que votre équipe reste concentrée.' },
  { icon: 'spark', title: 'Obtenez un bilan exploitable', text: 'Transformez la transcription en synthèse, décisions, actions, questions ouvertes et risques identifiés.' },
  { icon: 'search', title: 'Retrouvez le contexte', text: 'Interrogez la mémoire de vos réunions pour retrouver une décision ou comprendre l’historique d’un sujet.' },
  { icon: 'users', title: 'Travaillez en entreprise', text: 'Invitez votre équipe, attribuez les bons rôles et partagez les réunions dans un espace commun.' },
  { icon: 'shield', title: 'Protégez chaque espace', text: 'Vérification email par OTP, sessions sécurisées et isolation stricte des données entre entreprises.' },
  { icon: 'file', title: 'Partagez clairement', text: 'Consultez et exportez des comptes rendus structurés pour garder toutes les parties prenantes alignées.' },
];

const PLANS = [
  {
    name: 'Starter',
    description: 'Pour les petites équipes qui souhaitent structurer leurs premières réunions.',
    price: '1 000',
    suffix: 'FCFA / mois',
    features: ['Jusqu’à 5 membres', '120 minutes de transcription', 'Synthèses, décisions et actions', 'Exports des comptes rendus'],
  },
  {
    name: 'Business',
    description: 'Pour les entreprises qui centralisent leur mémoire et leurs décisions.',
    price: '1 500',
    suffix: 'FCFA / mois',
    featured: true,
    features: ['Jusqu’à 25 membres', '250 minutes de transcription', 'Assistant IA et mémoire entreprise', 'Rôles et gestion avancée de l’équipe'],
  },
  {
    name: 'Enterprise',
    description: 'Pour les organisations qui ont des besoins de volume, contrôle et accompagnement.',
    price: '2 000',
    suffix: 'FCFA / mois',
    features: ['Membres personnalisés', '400 minutes de transcription', 'Accompagnement au déploiement', 'Politiques de sécurité adaptées', 'Support et configuration dédiés'],
  },
];

export default function Landing() {
  const { status, user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [plans, setPlans] = useState(PLANS);
  const authenticated = status === 'authenticated';
  const appTarget = user?.onboarding_required ? '/onboarding' : '/app';

  useEffect(() => {
    billingService.plans().then((data) => {
      const remotePlans = data.plans || [];
      setPlans(PLANS.map((content) => {
        const remote = remotePlans.find((item) => item.code === content.name.toLowerCase());
        return remote ? { ...content, price: Number(remote.amount_xaf).toLocaleString('fr-FR') } : content;
      }));
    }).catch(() => {
      // Les tarifs locaux restent visibles si le backend est momentanément indisponible.
    });
  }, []);

  return (
    <div className="w-full min-w-0 max-w-full overflow-hidden bg-white text-encre">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-liseret/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-18 w-full min-w-0 max-w-7xl items-center justify-between px-5 sm:px-8">
          <Brand />
          <nav className="hidden items-center gap-8 md:flex" aria-label="Navigation principale">
            <a href="#produit" className="text-sm font-medium text-encre-sourde hover:text-encre">Produit</a>
            <a href="#fonctionnement" className="text-sm font-medium text-encre-sourde hover:text-encre">Fonctionnement</a>
            <a href="#tarifs" className="text-sm font-medium text-encre-sourde hover:text-encre">Tarifs</a>
            <a href="#securite" className="text-sm font-medium text-encre-sourde hover:text-encre">Sécurité</a>
          </nav>
          <div className="hidden items-center gap-3 md:flex">
            {authenticated ? <Link to={appTarget} className="rounded-xl bg-bordeaux-700 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(38,59,216,0.2)] hover:bg-bordeaux-800">Ouvrir mon espace</Link> : <><Link to="/connexion" className="px-3 py-2 text-sm font-semibold text-encre-douce hover:text-bordeaux-700">Se connecter</Link><Link to="/inscription" className="rounded-xl bg-bordeaux-700 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(38,59,216,0.2)] hover:bg-bordeaux-800">Créer un espace</Link></>}
          </div>
          <button onClick={() => setMenuOpen((value) => !value)} aria-expanded={menuOpen} aria-label="Ouvrir le menu" className="flex h-10 w-10 items-center justify-center rounded-xl border border-liseret md:hidden"><span className="text-xl">{menuOpen ? '×' : '☰'}</span></button>
        </div>
        {menuOpen && <div className="border-t border-liseret bg-white px-5 py-5 md:hidden"><nav className="flex flex-col gap-1"><MobileLink href="#produit" onClick={() => setMenuOpen(false)}>Produit</MobileLink><MobileLink href="#fonctionnement" onClick={() => setMenuOpen(false)}>Fonctionnement</MobileLink><MobileLink href="#tarifs" onClick={() => setMenuOpen(false)}>Tarifs</MobileLink><MobileLink href="#securite" onClick={() => setMenuOpen(false)}>Sécurité</MobileLink><Link to={authenticated ? appTarget : '/inscription'} className="mt-3 rounded-xl bg-bordeaux-700 px-4 py-3 text-center text-sm font-semibold text-white">{authenticated ? 'Ouvrir mon espace' : 'Créer un espace'}</Link>{!authenticated && <Link to="/connexion" className="py-2 text-center text-sm font-semibold text-encre-douce">Se connecter</Link>}</nav></div>}
      </header>

      <main>
        <section className="relative overflow-hidden bg-fond px-5 pb-20 pt-32 sm:px-8 lg:pb-28 lg:pt-40">
          <div className="absolute left-1/2 top-12 h-[520px] w-[920px] -translate-x-1/2 rounded-full bg-bordeaux-500/10 blur-3xl" />
          <div className="relative mx-auto max-w-7xl">
            <div className="mx-auto max-w-4xl text-center">
              <div className="inline-flex max-w-full items-center justify-center gap-2 rounded-full border border-bordeaux-400/25 bg-white px-3.5 py-2 text-center text-xs font-semibold text-bordeaux-700 shadow-sm"><span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" /><span>L’intelligence des réunions pour les entreprises</span></div>
              <h1 className="mt-7 text-4xl font-extrabold leading-[1.05] tracking-[-0.055em] text-encre sm:text-6xl lg:text-7xl">Vos réunions deviennent des décisions qui avancent.</h1>
              <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-encre-sourde sm:text-lg">MeetFlow capture, transcrit et structure chaque échange pour transformer vos réunions en actions claires, responsables et suivies.</p>
              <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
                <Link to={authenticated ? appTarget : '/inscription'} className="inline-flex items-center justify-center gap-2 rounded-xl bg-bordeaux-700 px-6 py-3.5 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(38,59,216,0.24)] transition hover:-translate-y-0.5 hover:bg-bordeaux-800">{authenticated ? 'Accéder à mon espace' : 'Créer mon espace entreprise'}<ArrowIcon /></Link>
                <a href="#produit" className="inline-flex items-center justify-center rounded-xl border border-liseret-clair bg-white px-6 py-3.5 text-sm font-semibold text-encre-douce shadow-sm hover:border-bordeaux-400 hover:text-bordeaux-700">Découvrir le produit</a>
              </div>
              <p className="mt-4 text-xs text-encre-sourde">Configuration guidée · Vérification sécurisée · Aucune carte bancaire requise</p>
            </div>
            <ProductPreview />
          </div>
        </section>

        <section className="border-y border-liseret bg-white px-5 py-7 sm:px-8">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-10 gap-y-4 text-sm font-semibold text-encre-sourde"><TrustItem text="Transcription automatique" /><TrustItem text="Analyse par NVIDIA NIM" /><TrustItem text="Espaces entreprise isolés" /><TrustItem text="Comptes rendus structurés" /></div>
        </section>

        <section id="produit" className="scroll-mt-20 px-5 py-20 sm:px-8 lg:py-28">
          <div className="mx-auto max-w-7xl"><SectionHeading eyebrow="Une plateforme complète" title="Moins de prise de notes. Plus de décisions." text="Un flux unique relie la réunion, son bilan et le travail qui doit réellement être accompli." /><div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">{FEATURES.map((feature) => <Feature key={feature.title} {...feature} />)}</div></div>
        </section>

        <section id="fonctionnement" className="scroll-mt-20 bg-bordeaux-950 px-5 py-20 text-white sm:px-8 lg:py-28">
          <div className="mx-auto grid max-w-7xl gap-14 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
            <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-bordeaux-400">Du son au résultat</p><h2 className="mt-4 text-3xl font-bold tracking-[-0.045em] sm:text-4xl">Un parcours simple pour toute l’équipe.</h2><p className="mt-5 max-w-lg leading-relaxed text-white/60">MeetFlow s’intègre au rythme de la réunion et rassemble automatiquement les informations importantes.</p></div>
            <div className="grid gap-4 sm:grid-cols-3"><ProcessStep number="01" title="Enregistrez" text="Lancez une réunion depuis votre espace." /><ProcessStep number="02" title="Laissez l’IA structurer" text="Transcription, synthèse et extraction sont automatisées." /><ProcessStep number="03" title="Décidez et partagez" text="Retrouvez les actions et diffusez un bilan clair." /></div>
          </div>
        </section>

        <section id="tarifs" className="scroll-mt-20 bg-white px-5 py-20 sm:px-8 lg:py-28">
          <div className="mx-auto max-w-7xl">
            <SectionHeading eyebrow="Tarifs de lancement" title="Une offre adaptée à la taille de votre équipe." text="Commencez avec l’essentiel, puis augmentez vos capacités lorsque vos usages se développent." />
            <div className="mt-5 flex justify-center"><span className="rounded-full border border-liseret bg-fond px-3.5 py-2 text-xs font-medium text-encre-sourde">Facturation mensuelle par entreprise · Paiement Mobile Money prochainement disponible</span></div>
            <div className="mt-12 grid gap-5 lg:grid-cols-3">
              {plans.map((plan) => {
                const code = plan.name.toLowerCase();
                const target = authenticated
                  ? (user?.onboarding_required ? `/onboarding?plan=${code}` : `/facturation?plan=${code}`)
                  : `/inscription?plan=${code}`;
                return <PricingCard key={plan.name} plan={plan} target={target} />;
              })}
            </div>
            <p className="mt-6 text-center text-xs leading-relaxed text-encre-sourde">Paiement mensuel sécurisé par MTN Mobile Money ou Orange Money. Chaque renouvellement est confirmé depuis votre téléphone.</p>
          </div>
        </section>

        <section id="securite" className="scroll-mt-20 bg-fond px-5 py-20 sm:px-8 lg:py-28">
          <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-2 lg:items-center">
            <div className="rounded-3xl border border-liseret bg-white p-7 shadow-[0_20px_60px_rgba(16,24,40,0.07)] sm:p-9"><div className="grid gap-4 sm:grid-cols-2"><SecurityCard icon="otp" title="Compte vérifié" text="Activation par code OTP envoyé par email." /><SecurityCard icon="tenant" title="Isolation entreprise" text="Chaque organisation possède son propre périmètre de données." /><SecurityCard icon="role" title="Accès par rôle" text="Administrateur, organisateur, membre et auditeur." /><SecurityCard icon="session" title="Session maîtrisée" text="Expiration automatique et accès protégé aux API." /></div></div>
            <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-bordeaux-700">Sécurité par conception</p><h2 className="mt-4 text-3xl font-bold tracking-[-0.045em] sm:text-4xl">Les bonnes informations, accessibles aux bonnes personnes.</h2><p className="mt-5 max-w-xl leading-relaxed text-encre-sourde">MeetFlow sépare les espaces entreprise et applique les permissions au niveau du serveur, pas uniquement dans l’interface.</p><Link to={authenticated ? appTarget : '/inscription'} className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-bordeaux-700 hover:text-bordeaux-900">Configurer mon espace <ArrowIcon /></Link></div>
          </div>
        </section>

        <section className="px-5 py-20 sm:px-8 lg:py-28"><div className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl bg-bordeaux-700 px-7 py-14 text-center text-white shadow-[0_24px_70px_rgba(38,59,216,0.25)] sm:px-12"><div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-white/10 blur-2xl" /><div className="relative"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-white/60">Votre prochaine réunion</p><h2 className="mx-auto mt-4 max-w-3xl text-3xl font-bold tracking-[-0.045em] sm:text-5xl">Commencez avec un espace aussi clair que vos décisions.</h2><p className="mx-auto mt-5 max-w-xl text-sm leading-relaxed text-white/70 sm:text-base">Créez votre compte, vérifiez votre email et configurez votre entreprise en quelques étapes.</p><Link to={authenticated ? appTarget : '/inscription'} className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-semibold text-bordeaux-800 shadow-lg hover:bg-fond">{authenticated ? 'Ouvrir MeetFlow' : 'Créer mon espace'} <ArrowIcon /></Link></div></div></section>
      </main>

      <footer className="border-t border-liseret bg-white px-5 py-10 sm:px-8"><div className="mx-auto flex max-w-7xl flex-col gap-6 sm:flex-row sm:items-center sm:justify-between"><Brand /><p className="text-xs text-encre-sourde">© {new Date().getFullYear()} MeetFlow AI. Intelligence de réunion pour les entreprises.</p><div className="flex gap-5 text-xs font-medium text-encre-sourde"><a href="#produit" className="hover:text-encre">Produit</a><a href="#tarifs" className="hover:text-encre">Tarifs</a><Link to="/connexion" className="hover:text-encre">Connexion</Link></div></div></footer>
    </div>
  );
}

function Brand() { return <Link to="/" className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-bordeaux-700 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(38,59,216,0.2)]">M</span><span><span className="block font-bold leading-tight text-encre">MeetFlow</span><span className="block text-[10px] font-medium uppercase tracking-[0.12em] text-encre-sourde">Intelligence</span></span></Link>; }
function MobileLink({ href, onClick, children }) { return <a href={href} onClick={onClick} className="rounded-lg px-3 py-3 text-sm font-medium text-encre-douce hover:bg-surface-haute">{children}</a>; }
function ArrowIcon() { return <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5" /></svg>; }
function TrustItem({ text }) { return <span className="flex items-center gap-2"><span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">✓</span>{text}</span>; }
function SectionHeading({ eyebrow, title, text }) { return <div className="mx-auto max-w-3xl text-center"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-bordeaux-700">{eyebrow}</p><h2 className="mt-4 text-3xl font-bold tracking-[-0.045em] sm:text-5xl">{title}</h2><p className="mx-auto mt-5 max-w-2xl leading-relaxed text-encre-sourde">{text}</p></div>; }
function Feature({ icon, title, text }) { return <article className="group rounded-2xl border border-liseret bg-white p-6 transition hover:-translate-y-1 hover:border-bordeaux-400/40 hover:shadow-[0_18px_45px_rgba(16,24,40,0.08)]"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-bordeaux-500/10 text-bordeaux-700"><FeatureIcon name={icon} /></span><h3 className="mt-5 text-lg font-semibold tracking-[-0.02em]">{title}</h3><p className="mt-2 text-sm leading-relaxed text-encre-sourde">{text}</p></article>; }
function ProcessStep({ number, title, text }) { return <div className="rounded-2xl border border-white/10 bg-white/5 p-6"><span className="font-donnees text-xs font-semibold text-bordeaux-400">{number}</span><h3 className="mt-8 text-lg font-semibold">{title}</h3><p className="mt-2 text-sm leading-relaxed text-white/55">{text}</p></div>; }
function SecurityCard({ icon, title, text }) { return <div className="rounded-2xl bg-fond p-5"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-bordeaux-700 shadow-sm"><FeatureIcon name={icon} /></span><h3 className="mt-4 text-sm font-semibold">{title}</h3><p className="mt-1.5 text-xs leading-relaxed text-encre-sourde">{text}</p></div>; }

function PricingCard({ plan, target }) {
  return <article className={`relative flex flex-col rounded-3xl border p-7 ${plan.featured ? 'border-bordeaux-700 bg-bordeaux-950 text-white shadow-[0_24px_60px_rgba(23,32,138,0.2)]' : 'border-liseret bg-white shadow-[0_14px_40px_rgba(16,24,40,0.05)]'}`}>
    {plan.featured && <span className="absolute right-5 top-5 rounded-full bg-white/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-white">Recommandé</span>}
    <p className={`text-sm font-semibold ${plan.featured ? 'text-bordeaux-400' : 'text-bordeaux-700'}`}>{plan.name}</p>
    <p className={`mt-3 min-h-12 text-sm leading-relaxed ${plan.featured ? 'text-white/60' : 'text-encre-sourde'}`}>{plan.description}</p>
    <div className="mt-7"><p className="font-donnees text-4xl font-semibold tracking-[-0.04em]">{plan.price}</p><p className={`mt-1 text-xs ${plan.featured ? 'text-white/45' : 'text-encre-sourde'}`}>{plan.suffix}</p></div>
    <ul className={`mt-7 flex-1 space-y-3 border-t pt-6 text-sm ${plan.featured ? 'border-white/10 text-white/75' : 'border-liseret text-encre-douce'}`}>{plan.features.map((feature) => <li key={feature} className="flex items-start gap-2.5"><span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] ${plan.featured ? 'bg-white/10 text-white' : 'bg-emerald-50 text-emerald-700'}`}>✓</span>{feature}</li>)}</ul>
    <Link to={target} className={`mt-8 inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3.5 text-sm font-semibold transition ${plan.featured ? 'bg-white text-bordeaux-800 hover:bg-fond' : 'border border-liseret-clair bg-white text-encre hover:border-bordeaux-400 hover:text-bordeaux-700'}`}>Choisir cette offre<ArrowIcon /></Link>
  </article>;
}

function ProductPreview() {
  return <div className="relative mx-auto mt-16 w-full min-w-0 max-w-5xl rounded-[28px] border border-liseret-clair bg-white p-2 shadow-[0_35px_90px_rgba(16,24,40,0.16)] sm:p-3"><div className="min-w-0 overflow-hidden rounded-[20px] border border-liseret bg-fond"><div className="flex h-12 min-w-0 items-center justify-between border-b border-liseret bg-white px-4"><div className="flex shrink-0 items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-red-300"/><span className="h-2.5 w-2.5 rounded-full bg-amber-300"/><span className="h-2.5 w-2.5 rounded-full bg-emerald-300"/></div><span className="truncate px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-encre-sourde">MeetFlow · Espace entreprise</span><span className="h-7 w-7 shrink-0 rounded-full bg-bordeaux-500/10"/></div><div className="grid min-h-[390px] min-w-0 sm:grid-cols-[180px_minmax(0,1fr)]"><div className="hidden border-r border-liseret bg-white p-4 sm:block"><div className="mb-7 h-7 w-24 rounded-lg bg-bordeaux-700"/><div className="space-y-2">{[true,false,false,false].map((active, index) => <div key={index} className={`h-9 rounded-lg ${active ? 'bg-bordeaux-500/10' : 'bg-surface-haute'}`}/>)}</div></div><div className="min-w-0 p-5 sm:p-7"><div className="flex min-w-0 items-end justify-between"><div className="min-w-0"><p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Vue d’ensemble</p><h3 className="mt-2 text-xl font-bold sm:text-2xl">Bonjour, votre bilan est prêt.</h3></div><span className="hidden shrink-0 rounded-lg bg-bordeaux-700 px-3 py-2 text-xs font-semibold text-white sm:block">+ Réunion</span></div><div className="mt-6 grid min-w-0 grid-cols-2 gap-3 lg:grid-cols-4">{['12 réunions','8 décisions','21 actions','4 membres'].map((value) => <div key={value} className="min-w-0 rounded-xl border border-liseret bg-white p-4"><p className="text-sm font-bold">{value.split(' ')[0]}</p><p className="mt-1 truncate text-[10px] text-encre-sourde">{value.slice(value.indexOf(' ')+1)}</p></div>)}</div><div className="mt-4 grid min-w-0 gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,0.7fr)]"><div className="min-w-0 rounded-xl border border-liseret bg-white p-5"><div className="flex min-w-0 items-center justify-between gap-2"><p className="truncate text-xs font-semibold">Réunion stratégie produit</p><span className="shrink-0 rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-semibold text-emerald-700">Terminée</span></div><div className="mt-5 space-y-3">{[95,78,86,62].map((width) => <div key={width} className="h-2 rounded-full bg-surface-haute"><div className="h-full rounded-full bg-bordeaux-400/40" style={{ width: `${width}%` }}/></div>)}</div></div><div className="min-w-0 rounded-xl bg-bordeaux-950 p-5 text-white"><p className="text-[10px] uppercase tracking-[0.1em] text-white/45">Décisions</p><p className="mt-3 text-2xl font-bold">3</p><p className="mt-2 text-xs leading-relaxed text-white/55">Priorités identifiées et prêtes à être partagées.</p></div></div></div></div></div></div>;
}

function FeatureIcon({ name }) {
  const paths = { mic: <><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></>, spark: <><path d="m12 3 1.4 4.6L18 9l-4.6 1.4L12 15l-1.4-4.6L6 9l4.6-1.4L12 3Z"/><path d="m5 15 .7 2.3L8 18l-2.3.7L5 21l-.7-2.3L2 18l2.3-.7L5 15Z"/></>, search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>, users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/></>, shield: <><path d="M12 3 5 6v5c0 4.7 2.8 8.2 7 10 4.2-1.8 7-5.3 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/></>, file: <><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 13h6M9 17h5"/></>, otp: <><rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 8h8M8 12h2M12 12h2M16 12h1M8 16h8"/></>, tenant: <><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 21V8h8v13M8 12h8"/></>, role: <><circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M17 11l2 2 3-4"/></>, session: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></> };
  return <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
