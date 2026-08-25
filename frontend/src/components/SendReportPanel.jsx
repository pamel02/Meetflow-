import { useState } from 'react';
import Card, { CardHeader } from './Card';
import Button from './Button';
import Input from './Input';
import EmailChipsField from './EmailChipsField';
import { exportService } from '../services';
import { useToast } from '../context/ToastContext';

/**
 * Panneau d'envoi du compte rendu (PDF) par email a plusieurs destinataires
 * a la fois, affiche a cote de la transcription et du compte rendu IA.
 */
export default function SendReportPanel({ meetingId, ready }) {
  const [emails, setEmails] = useState([]);
  const [subject, setSubject] = useState('Compte rendu de reunion');
  const [sending, setSending] = useState(false);
  const { notify } = useToast();

  const disabled = !ready;

  const handleSend = async () => {
    if (emails.length === 0) {
      notify.error('Ajoutez au moins une adresse email.');
      return;
    }
    setSending(true);
    try {
      await exportService.sendReport(meetingId, emails, subject);
      notify.success(
        emails.length > 1
          ? `Compte rendu envoye a ${emails.length} destinataires.`
          : 'Compte rendu envoye.'
      );
      setEmails([]);
    } catch (err) {
      notify.error(err.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader eyebrow="Export par email" title="Envoyer le PDF" />
      <div className="flex flex-col gap-4 p-5">
        <p className="text-xs text-encre-sourde">
          Ajoutez une ou plusieurs adresses puis envoyez le compte rendu en PDF simultanement a tout le monde.
        </p>
        <Input
          label="Objet"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={disabled}
        />
        <EmailChipsField label="Destinataires" emails={emails} onChange={setEmails} disabled={disabled} />
        {disabled && (
          <p className="rounded-xl border border-liseret bg-fond-doux px-3 py-2 text-xs text-encre-sourde">
            Le PDF sera disponible des que le compte rendu sera termine.
          </p>
        )}
        <Button onClick={handleSend} loading={sending} disabled={disabled || emails.length === 0}>
          {emails.length > 0
            ? `Envoyer a ${emails.length} destinataire${emails.length > 1 ? 's' : ''}`
            : 'Envoyer le compte rendu'}
        </Button>
      </div>
    </Card>
  );
}
