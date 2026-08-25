import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TopBar from '../components/TopBar';
import Card, { CardHeader } from '../components/Card';
import Input from '../components/Input';
import Button from '../components/Button';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { authService, monitoringService } from '../services';

export default function Settings() {
  const { user, refreshProfile, logout } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  return (
    <>
      <TopBar title="Paramètres" />
      <main className="flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8">
        <div className="mx-auto w-full max-w-5xl">
          <div className="mb-7"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Configuration</p><h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre">Paramètres du compte</h2><p className="mt-2 text-sm text-encre-sourde">Gérez votre profil, la sécurité et les services intelligents.</p></div>
        <div className="flex flex-col gap-6">
          <ProfileSection user={user} onSaved={refreshProfile} notify={notify} />
          <PasswordSection notify={notify} />
          <DangerSection notify={notify} onDeleted={() => { logout(true); navigate('/connexion'); }} />
          <DiagnosticsSection />
        </div></div>
      </main>
    </>
  );
}

function ProfileSection({ user, onSaved, notify }) {
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [language, setLanguage] = useState(user?.language || 'fr');
  const [saving, setSaving] = useState(false);

  const dirty =
    name !== (user?.name || '') || email !== (user?.email || '') || language !== (user?.language || 'fr');

  const handleSave = async () => {
    setSaving(true);
    try {
      await authService.updateProfile({ name, email, language });
      await onSaved();
      notify.success('Profil mis a jour.');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader eyebrow="Compte" title="Profil" />
      <div className="grid grid-cols-1 gap-5 px-5 py-5 md:grid-cols-2">
        <Input label="Nom" value={name} onChange={(e) => setName(e.target.value)} />
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          hint="Utilisee pour la connexion et les notifications."
        />
        <label className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-encre-douce">
            Langue preferee
          </span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-xl border border-liseret bg-white px-3.5 py-3 text-sm text-encre shadow-sm focus:border-bordeaux-500"
          >
            <option value="fr">Francais</option>
            <option value="en">English</option>
          </select>
        </label>
        <div className="md:col-span-2">
          <Button disabled={!dirty} loading={saving} onClick={handleSave}>Enregistrer</Button>
        </div>
      </div>
    </Card>
  );
}

function PasswordSection({ notify }) {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await authService.updatePassword(oldPassword, newPassword);
      setOldPassword('');
      setNewPassword('');
      notify.success('Mot de passe mis a jour.');
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader eyebrow="Securite" title="Mot de passe" />
      <div className="grid grid-cols-1 gap-5 px-5 py-5 md:grid-cols-2">
        <Input
          label="Mot de passe actuel"
          type="password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
        />
        <Input
          label="Nouveau mot de passe"
          type="password"
          minLength={8}
          hint="8 caracteres minimum"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
        <div className="md:col-span-2">
          <Button loading={saving} disabled={!oldPassword || !newPassword} onClick={handleSave}>
            Changer le mot de passe
          </Button>
        </div>
      </div>
    </Card>
  );
}

function DangerSection({ notify, onDeleted }) {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await authService.deleteAccount(password);
      onDeleted();
    } catch (err) {
      notify.error(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="border-red-200">
      <CardHeader eyebrow="Zone sensible" title="Supprimer le compte" />
      <div className="px-5 py-5">
        <p className="text-sm text-encre-douce">
          Cette action supprime definitivement votre compte ainsi que toutes vos reunions, transcriptions,
          fichiers audio et comptes rendus. Elle est irreversible.
        </p>
        <Button variant="danger" className="mt-4" onClick={() => setOpen(true)}>
          Supprimer mon compte
        </Button>
      </div>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Confirmer la suppression"
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>Annuler</Button>
            <Button variant="danger" loading={deleting} disabled={!password} onClick={handleDelete}>
              Supprimer definitivement
            </Button>
          </>
        }
      >
        <p className="mb-4 text-sm text-encre-douce">
          Saisissez votre mot de passe pour confirmer la suppression definitive de votre compte.
        </p>
        <Input
          label="Mot de passe"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Modal>
    </Card>
  );
}

function DiagnosticsSection() {
  const [health, setHealth] = useState(null);
  const [models, setModels] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([monitoringService.health(), monitoringService.models()])
      .then(([healthData, modelsData]) => {
        setHealth(healthData);
        setModels(modelsData.models);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Card>
      <CardHeader eyebrow="Diagnostic" title="Etat du systeme" />
      <div className="px-5 py-5">
        {error && <p className="text-sm text-bordeaux-400">{error}</p>}
        {health && (
          <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-5">
            {Object.entries(health.components).map(([key, comp]) => (
              <div key={key} className="rounded-xl border border-liseret bg-fond-doux px-3 py-3">
                <p className="font-donnees text-[10px] uppercase tracking-[0.1em] text-encre-sourde">{key}</p>
                <p className={`mt-1 text-xs ${comp.ok ? 'text-encre-douce' : 'text-bordeaux-400'}`}>
                  {comp.message}
                </p>
              </div>
            ))}
          </div>
        )}
        {models && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <InfoLine label="Modele LLM" value={models.llm} />
            <InfoLine label="Modele d'embedding" value={models.embedding} />
            <InfoLine label="Transcripteur" value={models.transcriber} />
            <div className="md:col-span-3">
              <p className="font-donnees text-[10px] uppercase tracking-[0.1em] text-encre-sourde">
                Modèles disponibles via NVIDIA NIM
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {(models.nvidia_available || []).length === 0 ? (
                  <span className="text-xs text-encre-sourde">Aucun modèle disponible.</span>
                ) : (
                  models.nvidia_available.map((m) => (
                    <span key={m} className="rounded-full border border-liseret-clair bg-fond px-2.5 py-1 font-donnees text-xs text-encre-sourde">
                      {m}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

function InfoLine({ label, value }) {
  return (
    <div>
      <p className="font-donnees text-[10px] uppercase tracking-[0.1em] text-encre-sourde">{label}</p>
      <p className="mt-1 text-sm text-encre">{value}</p>
    </div>
  );
}
