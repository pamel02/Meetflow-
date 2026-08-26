import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import Button from '../components/Button';
import Card, { CardHeader } from '../components/Card';
import Input from '../components/Input';
import Modal from '../components/Modal';
import TopBar from '../components/TopBar';
import { useToast } from '../context/ToastContext';
import { billingService } from '../services';

const FEATURES = {
  starter: ['5 membres', '120 min de transcription', 'Synthèses et exports'],
  business: ['25 membres', '250 min de transcription', 'Assistant et mémoire entreprise'],
  enterprise: ['100 membres', '400 min de transcription', 'Accompagnement prioritaire'],
};
const STATUS_LABELS = { PENDING: 'En attente', COMPLETED: 'Payé', FAILED: 'Échoué', REVERSED: 'Remboursé' };

export default function Billing() {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [plans, setPlans] = useState([]);
  const [account, setAccount] = useState(null);
  const [payments, setPayments] = useState([]);
  const [selected, setSelected] = useState(null);
  const [operator, setOperator] = useState('mtn');
  const [phone, setPhone] = useState('');
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [pendingId, setPendingId] = useState(null);
  const returnTo = location.state?.from || searchParams.get('retour') || sessionStorage.getItem('meetflow_payment_return_to') || '/app';

  const load = useCallback(async () => {
    try {
      const [planData, currentData, paymentData] = await Promise.all([
        billingService.plans(), billingService.current(), billingService.payments(),
      ]);
      setPlans(planData.plans || []);
      setAccount(currentData);
      setPayments(paymentData.payments || []);
    } catch (error) {
      notify.error(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (location.state?.from) sessionStorage.setItem('meetflow_payment_return_to', location.state.from);
  }, [location.state?.from]);

  useEffect(() => {
    if (!plans.length || selected) return;
    const code = searchParams.get('plan') || sessionStorage.getItem('meetflow_selected_plan');
    const plan = plans.find((item) => item.code === code);
    if (plan) setSelected(plan);
  }, [plans, searchParams, selected]);

  useEffect(() => {
    if (!pendingId) return undefined;
    let attempts = 0;
    const timer = setInterval(async () => {
      attempts += 1;
      try {
        const data = await billingService.payment(pendingId);
        if (['COMPLETED', 'FAILED', 'REVERSED'].includes(data.payment.status)) {
          clearInterval(timer);
          setPendingId(null);
          await load();
          if (data.payment.status === 'COMPLETED') {
            sessionStorage.removeItem('meetflow_activation_pending');
            sessionStorage.removeItem('meetflow_selected_plan');
            sessionStorage.removeItem('meetflow_payment_return_to');
            notify.success('Paiement confirmé. Votre rapport est maintenant déverrouillé.');
            navigate(returnTo, { replace: true, state: { paymentConfirmed: true } });
          }
          else notify.error(data.payment.failure_reason || 'Le paiement n’a pas abouti.');
        }
      } catch {
        // Le webhook peut encore confirmer le paiement : le prochain cycle réessaie.
      }
      if (attempts >= 45) {
        clearInterval(timer);
        setPendingId(null);
        load();
      }
    }, 4000);
    return () => clearInterval(timer);
  }, [pendingId, load, navigate, notify, returnTo]);

  const choosePlan = (plan) => {
    setSelected(plan); setQuote(null);
    setSearchParams({ plan: plan.code });
  };

  const closeCheckout = () => {
    setSelected(null);
    setQuote(null);
    sessionStorage.removeItem('meetflow_selected_plan');
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('plan');
    setSearchParams(nextParams, { replace: true });
  };

  const getQuote = async () => {
    setWorking(true);
    try {
      const data = await billingService.quote({ plan_code: selected.code, operator, phone_number: phone });
      setQuote(data.quote);
    } catch (error) { notify.error(error.message); }
    finally { setWorking(false); }
  };

  const pay = async () => {
    setWorking(true);
    try {
      const data = await billingService.checkout({ plan_code: selected.code, operator, phone_number: phone });
      setPendingId(data.payment.id);
      setPayments((items) => [data.payment, ...items]);
      closeCheckout();
      notify.info('Validez maintenant la demande USSD sur votre téléphone.');
    } catch (error) { notify.error(error.message); }
    finally { setWorking(false); }
  };

  const subscription = account?.subscription;
  return <>
    <TopBar title="Facturation" />
    <main className="flex-1 overflow-y-auto px-4 py-7 sm:px-6 md:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-bordeaux-700">Abonnement entreprise</p><h2 className="mt-2 text-3xl font-bold tracking-[-0.04em] text-encre">Une facturation simple en FCFA</h2><p className="mt-2 text-sm text-encre-sourde">Paiement sécurisé par MTN Mobile Money ou Orange Money.</p></div>
          <span className={`w-fit rounded-full px-3 py-1.5 text-xs font-semibold ${account?.mode === 'LIVE' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{account?.mode === 'LIVE' ? 'Mode réel' : 'Mode sandbox'}</span>
        </div>

        {location.state?.subscriptionRequired && <div className="mt-6 rounded-2xl border border-bordeaux-400/30 bg-bordeaux-500/5 px-5 py-4 text-sm text-bordeaux-800"><strong>Abonnement requis :</strong> choisissez et réglez une offre pour continuer à utiliser les fonctions premium.</div>}
        {location.state?.reportUnlock && <div className="mt-6 rounded-2xl border border-bordeaux-400/30 bg-bordeaux-500/5 px-5 py-4 text-sm text-bordeaux-800"><strong>Votre compte rendu est prêt :</strong> choisissez une offre pour le consulter, le télécharger et l’envoyer par e-mail. Vous reviendrez automatiquement au rapport après le paiement.</div>}
        {(location.state?.quotaExhausted || account?.usage?.transcription_quota_exhausted) && <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900"><strong>Pack de minutes épuisé :</strong> choisissez et réglez de nouveau une offre pour continuer à enregistrer et transcrire vos réunions.</div>}

        {!loading && !account?.provider_ready && <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900"><strong>Connexion au paiement incomplète :</strong> {account?.provider_configuration_error || 'Ajoutez la clé Riserva dans backend/.env.'} L’interface et les abonnements restent consultables.</div>}

        <Card className="mt-6 overflow-hidden">
          <div className="grid gap-5 p-6 md:grid-cols-[1fr_auto] md:items-center">
            <div><p className="text-xs font-semibold uppercase tracking-[0.1em] text-encre-sourde">Abonnement actuel</p><p className="mt-2 text-2xl font-bold text-encre">{subscription ? subscription.plan.name : 'Aucune offre active'}</p><p className="mt-1 text-sm text-encre-sourde">{subscription ? `Valable jusqu’au ${new Date(subscription.current_period_end).toLocaleDateString('fr-FR')}` : 'Choisissez une offre pour activer la facturation de votre entreprise.'}</p></div>
            {subscription && <div><div className="grid grid-cols-2 gap-3"><Metric label="Membres" value={`${account.usage.members} / ${subscription.plan.max_members}`} /><Metric label="Transcription" value={`${account.usage.transcription_minutes} / ${subscription.plan.transcription_minutes} min`} /></div><Link to="/app" className="mt-3 inline-flex w-full items-center justify-center rounded-xl bg-bordeaux-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-bordeaux-800">Accéder à l’application</Link></div>}
          </div>
        </Card>

        <section className="mt-8"><h3 className="text-xl font-bold text-encre">Choisir une offre</h3><div className="mt-4 grid gap-5 lg:grid-cols-3">{plans.map((plan) => <PlanCard key={plan.code} plan={plan} active={subscription?.plan.code === plan.code} featured={plan.code === 'business'} disabled={account?.role !== 'admin'} onChoose={() => choosePlan(plan)} />)}</div></section>

        <Card className="mt-8 overflow-hidden"><CardHeader eyebrow="Transactions" title="Historique des paiements" /><div className="overflow-x-auto">{payments.length ? <table className="w-full min-w-[680px] text-left text-sm"><thead className="bg-fond text-xs uppercase tracking-[0.08em] text-encre-sourde"><tr><th className="px-5 py-3">Date</th><th className="px-5 py-3">Offre</th><th className="px-5 py-3">Moyen</th><th className="px-5 py-3">Montant</th><th className="px-5 py-3">Statut</th></tr></thead><tbody className="divide-y divide-liseret">{payments.map((payment) => <tr key={payment.id}><td className="px-5 py-4 text-encre-sourde">{new Date(payment.created_at).toLocaleString('fr-FR')}</td><td className="px-5 py-4 font-semibold text-encre">{payment.plan.name}</td><td className="px-5 py-4 uppercase text-encre-sourde">{payment.operator} · {payment.phone}</td><td className="px-5 py-4 font-semibold text-encre">{formatMoney(payment.amount)}</td><td className="px-5 py-4"><Status status={payment.status} /></td></tr>)}</tbody></table> : <p className="px-5 py-10 text-center text-sm text-encre-sourde">Aucun paiement enregistré.</p>}</div></Card>
      </div>
    </main>

    <Modal open={Boolean(selected)} onClose={closeCheckout} title={selected ? `Souscrire à l’offre ${selected.name}` : 'Souscrire'} footer={<><Button variant="secondary" onClick={closeCheckout}>Annuler</Button>{quote ? <Button loading={working} onClick={pay}>Payer {selected && formatMoney(selected.amount_xaf)}</Button> : <Button loading={working} onClick={getQuote}>Vérifier le montant</Button>}</>}>
      {selected && <div className="space-y-5"><div className="rounded-xl bg-fond p-4"><div className="flex items-center justify-between"><span className="text-sm text-encre-sourde">Abonnement mensuel</span><strong className="text-lg text-encre">{formatMoney(selected.amount_xaf)}</strong></div></div><div><p className="mb-2 text-xs font-semibold text-encre-douce">Moyen de paiement</p><div className="grid grid-cols-2 gap-3"><OperatorButton label="MTN MoMo" active={operator === 'mtn'} onClick={() => { setOperator('mtn'); setQuote(null); }} /><OperatorButton label="Orange Money" active={operator === 'orange'} onClick={() => { setOperator('orange'); setQuote(null); }} /></div></div><Input label="Numéro Mobile Money" inputMode="tel" value={phone} onChange={(event) => { setPhone(event.target.value); setQuote(null); }} placeholder="6XX XXX XXX" hint="Le téléphone recevra une demande de confirmation sécurisée." />{quote && <QuoteSummary quote={quote} amount={selected.amount_xaf} />}</div>}
    </Modal>
  </>;
}

function PlanCard({ plan, active, featured, disabled, onChoose }) {
  return <Card className={`relative flex flex-col p-6 ${featured ? 'border-bordeaux-400 shadow-[0_18px_45px_rgba(38,59,216,0.1)]' : ''}`}>{featured && <span className="absolute right-4 top-4 rounded-full bg-bordeaux-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase text-bordeaux-700">Recommandé</span>}<p className="text-sm font-semibold text-bordeaux-700">{plan.name}</p><p className="mt-4 text-3xl font-bold tracking-[-0.04em] text-encre">{formatMoney(plan.amount_xaf)}</p><p className="mt-1 text-xs text-encre-sourde">par mois · par entreprise</p><ul className="my-6 flex-1 space-y-3 border-t border-liseret pt-5 text-sm text-encre-douce">{FEATURES[plan.code]?.map((item) => <li key={item} className="flex gap-2"><span className="text-emerald-600">✓</span>{item}</li>)}</ul><Button variant={active ? 'secondary' : 'primary'} disabled={disabled} onClick={onChoose}>{active ? 'Renouveler cette offre' : 'Choisir cette offre'}</Button>{disabled && <p className="mt-2 text-center text-[11px] text-encre-sourde">Réservé à l’administrateur</p>}</Card>;
}
function Metric({ label, value }) { return <div className="rounded-xl bg-fond px-4 py-3"><p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-encre-sourde">{label}</p><p className="mt-1 text-sm font-bold text-encre">{value}</p></div>; }
function OperatorButton({ label, active, onClick }) { return <button type="button" onClick={onClick} className={`rounded-xl border px-4 py-3 text-sm font-semibold transition ${active ? 'border-bordeaux-700 bg-bordeaux-500/5 text-bordeaux-700' : 'border-liseret text-encre-sourde hover:border-bordeaux-400'}`}>{label}</button>; }
function QuoteSummary({ quote, amount }) { const fee = quote.fee ?? quote.fees; const credited = quote.total ?? quote.total_amount; return <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm"><div className="flex justify-between text-emerald-900"><span>Montant débité au client</span><strong>{formatMoney(amount)}</strong></div>{fee != null && <div className="mt-2 flex justify-between text-xs text-emerald-700"><span>Frais de collecte déduits</span><span>{formatMoney(fee)}</span></div>}{credited != null && <div className="mt-2 flex justify-between text-xs text-emerald-700"><span>Net crédité</span><span>{formatMoney(credited)}</span></div>}<p className="mt-3 text-xs leading-relaxed text-emerald-800">Après validation, confirmez la demande USSD sur votre téléphone. Aucun code secret ne vous sera demandé par MeetFlow.</p></div>; }
function Status({ status }) { const tone = status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700' : status === 'FAILED' || status === 'REVERSED' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'; return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${tone}`}>{STATUS_LABELS[status] || status}</span>; }
function formatMoney(value) { return `${Number(value || 0).toLocaleString('fr-FR')} FCFA`; }
