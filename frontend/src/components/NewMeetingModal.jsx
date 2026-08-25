import { useState } from 'react';
import Modal from './Modal';
import Input from './Input';
import Button from './Button';
import EmailChipsField from './EmailChipsField';

export default function NewMeetingModal({ open, onClose, onCreate }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [notifyEmails, setNotifyEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const reset = () => {
    setTitle('');
    setDescription('');
    setNotifyEmails([]);
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onCreate(title.trim(), description.trim(), notifyEmails);
      reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={handleClose} title="Nouvelle reunion" width="max-w-xl">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Titre (optionnel)"
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Laissez vide pour une generation automatique"
        />
        <label className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-encre-douce">
            Description courte
          </span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="resize-none rounded-xl border border-liseret bg-white px-3.5 py-3 text-sm text-encre shadow-sm placeholder:text-taupe-500 focus:border-bordeaux-500"
            placeholder="De quoi va parler cette reunion ?"
          />
        </label>

        <div className="border-t border-liseret pt-4">
          <p className="font-donnees text-[11px] uppercase tracking-[0.12em] text-encre-sourde">
            Envoi automatique du compte rendu
          </p>
          <p className="mt-1 mb-3 text-xs text-encre-sourde">
            Des destinataires facultatifs a qui le PDF sera envoye automatiquement des qu'il sera pret.
          </p>
          <EmailChipsField emails={notifyEmails} onChange={setNotifyEmails} />
        </div>

        {error && <p className="text-sm text-bordeaux-400">{error}</p>}
        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={handleClose}>Annuler</Button>
          <Button type="submit" loading={loading}>Creer la reunion</Button>
        </div>
      </form>
    </Modal>
  );
}
