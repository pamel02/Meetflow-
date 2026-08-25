import { useCallback, useEffect, useState } from 'react';
import TopBar from '../components/TopBar';
import Button from '../components/Button';
import Card, { CardHeader } from '../components/Card';
import Input from '../components/Input';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { organizationService } from '../services';

const ROLE_LABELS = { admin: 'Administrateur', organizer: 'Organisateur', member: 'Membre', auditor: 'Auditeur' };

export default function Team() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [data, setData] = useState({ members: [], invitations: [] });
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('member');
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);
  const isAdmin = user?.organization_role === 'admin';

  const load = useCallback(async () => {
    try { setData(await organizationService.members()); }
    catch (err) { notify.error(err.message); }
    finally { setLoading(false); }
  }, [notify]);

  useEffect(() => { load(); }, [load]);

  const invite = async (event) => {
    event.preventDefault(); setInviting(true);
    try { const result = await organizationService.invite(email, role); notify.success(result.message); setEmail(''); await load(); }
    catch (err) { notify.error(err.message); }
    finally { setInviting(false); }
  };

  const changeRole = async (membershipId, nextRole) => {
    try { await organizationService.updateRole(membershipId, nextRole); notify.success('Rôle mis à jour.'); await load(); }
    catch (err) { notify.error(err.message); }
  };

  const remove = async (membership) => {
    if (!window.confirm(`Retirer ${membership.user.name} de l’entreprise ?`)) return;
    try { await organizationService.removeMember(membership.id); notify.success('Membre retiré.'); await load(); }
    catch (err) { notify.error(err.message); }
  };

  return (
    <><TopBar title="Équipe" /><main className="flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8"><div className="mx-auto max-w-6xl">
      <div className="mb-7"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Espace entreprise</p><h1 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre">Équipe de {user?.organization?.name}</h1><p className="mt-2 text-sm text-encre-sourde">Gérez les accès et les responsabilités de chaque collaborateur.</p></div>
      {isAdmin && <Card className="mb-6"><CardHeader eyebrow="Invitation" title="Ajouter un collaborateur" /><form onSubmit={invite} className="grid gap-4 px-5 py-5 md:grid-cols-[1fr_220px_auto] md:items-end"><Input label="Email professionnel" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="collaborateur@entreprise.com" /><label className="flex flex-col gap-2"><span className="text-xs font-semibold text-encre-douce">Rôle</span><select value={role} onChange={(e) => setRole(e.target.value)} className="rounded-xl border border-liseret bg-white px-3.5 py-3 text-sm"><option value="organizer">Organisateur</option><option value="member">Membre</option><option value="auditor">Auditeur</option></select></label><Button type="submit" loading={inviting} className="h-[46px]">Envoyer l’invitation</Button></form></Card>}
      <Card><CardHeader eyebrow={`${data.members.length} membre${data.members.length > 1 ? 's' : ''}`} title="Membres actifs" />
        <div className="divide-y divide-liseret">{loading ? <p className="p-6 text-sm text-encre-sourde">Chargement…</p> : data.members.map((membership) => <div key={membership.id} className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-bordeaux-500/10 text-sm font-bold text-bordeaux-700">{initials(membership.user.name)}</span><div className="min-w-0 flex-1"><p className="truncate font-semibold text-encre">{membership.user.name}{membership.user.id === user.id && <span className="ml-2 text-xs font-normal text-encre-sourde">Vous</span>}</p><p className="truncate text-sm text-encre-sourde">{membership.user.email}</p></div>{isAdmin && membership.user.id !== user.id ? <><select aria-label={`Rôle de ${membership.user.name}`} value={membership.role} onChange={(e) => changeRole(membership.id, e.target.value)} className="rounded-lg border border-liseret bg-white px-3 py-2 text-sm"><option value="admin">Administrateur</option><option value="organizer">Organisateur</option><option value="member">Membre</option><option value="auditor">Auditeur</option></select><button onClick={() => remove(membership)} className="text-sm font-medium text-red-600 hover:text-red-700">Retirer</button></> : <span className="rounded-full bg-surface-haute px-3 py-1.5 text-xs font-semibold text-encre-douce">{ROLE_LABELS[membership.role]}</span>}</div>)}</div>
      </Card>
      {data.invitations.length > 0 && <Card className="mt-6"><CardHeader eyebrow="En attente" title="Invitations envoyées" /><div className="divide-y divide-liseret">{data.invitations.map((invitation) => <div key={invitation.id} className="flex items-center justify-between gap-4 p-5"><div><p className="font-medium text-encre">{invitation.email}</p><p className="mt-1 text-xs text-encre-sourde">{ROLE_LABELS[invitation.role]}</p></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">En attente</span></div>)}</div></Card>}
    </div></main></>
  );
}

function initials(name = '') { return name.split(' ').filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase(); }
