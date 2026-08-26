import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import Button from '../components/Button';
import { Loader } from '../components/Loader';
import { useAuth } from '../context/AuthContext';

const ROLE_LABELS = {
  organizer: 'Organisateur',
  member: 'Membre',
  auditor: 'Auditeur',
};

export default function Invitation() {
  const { status, user, logout, refreshProfile } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = (searchParams.get('email') || '').trim().toLowerCase();
  const organization = searchParams.get('entreprise') || 'votre entreprise';
  const role = ROLE_LABELS[searchParams.get('role')] || 'Membre';
  const query = searchParams.toString();
  const accountMatches = user?.email?.toLowerCase() === email;

  if (status === 'checking') {
    return <div className="flex min-h-dvh items-center justify-center bg-fond"><Loader label="Vérification de l’invitation…" /></div>;
  }

  const openWorkspace = async () => {
    await refreshProfile();
    navigate('/app', { replace: true });
  };

  const changeAccount = async () => {
    await logout();
    navigate(`/invitation?${query}`, { replace: true });
  };

  return (
    <main className="min-h-dvh bg-fond px-5 py-8 sm:px-8">
      <header className="mx-auto flex max-w-5xl items-center justify-between">
        <Link to="/" className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-bordeaux-700 font-extrabold text-white">M</span><span className="font-bold text-encre">MeetFlow</span></Link>
        <span className="rounded-full border border-liseret bg-white px-3 py-1.5 text-xs font-semibold text-encre-sourde">Invitation sécurisée</span>
      </header>

      <section className="mx-auto mt-10 max-w-2xl overflow-hidden rounded-3xl border border-liseret bg-white shadow-[0_24px_70px_rgba(16,24,40,0.09)] sm:mt-16">
        <div className="bg-gradient-to-br from-bordeaux-950 via-bordeaux-800 to-bordeaux-700 px-7 py-9 text-white sm:px-10">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/12"><TeamIcon /></div>
          <p className="mt-6 text-xs font-semibold uppercase tracking-[0.14em] text-white/60">Invitation entreprise</p>
          <h1 className="mt-2 text-3xl font-bold tracking-[-0.04em]">Rejoignez {organization}</h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/72">Vous avez été invité à collaborer dans cet espace MeetFlow avec le rôle de <strong className="text-white">{role}</strong>.</p>
        </div>

        <div className="p-7 sm:p-10">
          {!email ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">Ce lien d’invitation est incomplet. Demandez à l’administrateur de vous renvoyer l’invitation.</div>
          ) : status === 'authenticated' && !accountMatches ? (
            <>
              <h2 className="text-xl font-bold text-encre">Cette invitation est destinée à une autre adresse</h2>
              <p className="mt-3 text-sm leading-relaxed text-encre-sourde">Vous êtes connecté avec <strong className="text-encre">{user.email}</strong>, mais l’invitation a été envoyée à <strong className="text-encre">{email}</strong>.</p>
              <Button size="lg" className="mt-6 w-full" onClick={changeAccount}>Se déconnecter et continuer</Button>
            </>
          ) : status === 'authenticated' ? (
            <>
              <h2 className="text-xl font-bold text-encre">Votre compte correspond à l’invitation</h2>
              <p className="mt-3 text-sm leading-relaxed text-encre-sourde">Ouvrez maintenant l’espace de {organization}. Vos autorisations seront appliquées automatiquement.</p>
              <Button size="lg" className="mt-6 w-full" onClick={openWorkspace}>Ouvrir l’espace entreprise</Button>
            </>
          ) : (
            <>
              <h2 className="text-xl font-bold text-encre">Accepter l’invitation</h2>
              <p className="mt-3 text-sm leading-relaxed text-encre-sourde">Utilisez obligatoirement l’adresse <strong className="text-encre">{email}</strong>. Si vous avez déjà un compte, connectez-vous. Sinon, créez-le puis validez le code OTP reçu par e-mail.</p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <Link to={`/inscription?${query}`} className="inline-flex items-center justify-center rounded-xl bg-bordeaux-700 px-5 py-3.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(38,59,216,0.2)] hover:bg-bordeaux-800">Créer mon compte</Link>
                <Link to={`/connexion?${query}`} className="inline-flex items-center justify-center rounded-xl border border-liseret bg-white px-5 py-3.5 text-sm font-semibold text-encre hover:border-bordeaux-400 hover:text-bordeaux-700">J’ai déjà un compte</Link>
              </div>
            </>
          )}
          <div className="mt-7 border-t border-liseret pt-5"><p className="text-xs leading-relaxed text-encre-sourde">L’accès est lié à l’adresse invitée. MeetFlow ne vous demandera jamais votre mot de passe ou votre code OTP par e-mail.</p></div>
        </div>
      </section>
    </main>
  );
}

function TeamIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
}
