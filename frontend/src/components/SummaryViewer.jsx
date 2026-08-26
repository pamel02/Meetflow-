import Card, { CardHeader } from './Card';
import Button from './Button';
import FormattedText from './FormattedText';
import { severityTone } from '../utils/status';

function Section({ eyebrow, title, children }) {
  return (
    <Card>
      <CardHeader eyebrow={eyebrow} title={title} />
      <div className="px-5 py-4">{children}</div>
    </Card>
  );
}

function EmptyRow({ label }) {
  return <p className="text-sm text-encre-sourde">{label}</p>;
}

export default function SummaryViewer({ report, pending, onUnlock }) {
  if (pending) {
    return (
      <p className="py-8 text-center text-sm text-encre-sourde">
        Le bilan IA est en cours de generation. Cette section se mettra a jour automatiquement.
      </p>
    );
  }

  if (report?.locked) {
    const preview = report.preview || {};
    const metrics = [
      ['Décisions', preview.decisions_count || 0],
      ['Actions', preview.actions_count || 0],
      ['Questions', preview.questions_count || 0],
      ['Risques', preview.risks_count || 0],
    ];
    return (
      <Card className="relative overflow-hidden border-bordeaux-400/40">
        <div className="bg-gradient-to-br from-bordeaux-950 via-bordeaux-800 to-bordeaux-700 px-6 py-7 text-white sm:px-8">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/12 text-xl" aria-hidden="true">🔒</div>
          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-white/65">Analyse terminée</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]">Votre compte rendu est prêt</h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/75">Débloquez le rapport premium, ses décisions, ses actions, les exports PDF et son envoi automatique par e-mail.</p>
        </div>
        <div className="p-6 sm:p-8">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {metrics.map(([label, value]) => <div key={label} className="rounded-2xl border border-liseret bg-fond px-4 py-3"><p className="text-2xl font-bold text-encre">{value}</p><p className="mt-1 text-xs text-encre-sourde">{label}</p></div>)}
          </div>
          <div className="relative mt-5 overflow-hidden rounded-2xl border border-liseret bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-encre-sourde">Aperçu du résumé</p>
            <p className="mt-3 max-h-20 overflow-hidden text-sm leading-7 text-encre-douce">{preview.summary_excerpt || 'Le rapport structuré a été généré avec succès.'}</p>
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-white to-transparent" />
          </div>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-relaxed text-encre-sourde">Paiement sécurisé par MTN MoMo ou Orange Money.</p>
            <Button size="lg" onClick={onUnlock}>Débloquer mon rapport</Button>
          </div>
        </div>
      </Card>
    );
  }

  if (!report?.summary) {
    return <p className="py-8 text-center text-sm text-encre-sourde">Aucun compte rendu disponible.</p>;
  }

  const { summary, decisions = [], actions = [], questions = [], risks = [] } = report;

  return (
    <div className="flex flex-col gap-4">
      <Section eyebrow="Bilan" title="Resume general">
        <p className="text-sm leading-relaxed text-encre-douce"><FormattedText text={summary.general_summary} /></p>
        {summary.participants?.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {summary.participants.map((p) => (
              <span key={p} className="rounded-full border border-bordeaux-400/40 bg-bordeaux-500/5 px-3 py-1 text-xs font-medium text-bordeaux-700">
                {p}
              </span>
            ))}
          </div>
        )}
      </Section>

      <Section eyebrow={`${decisions.length} element(s)`} title="Decisions">
        {decisions.length === 0 ? (
          <EmptyRow label="Aucune decision identifiee." />
        ) : (
          <ul className="flex flex-col gap-3">
            {decisions.map((d) => (
              <li key={d.id} className="border-l-2 border-bordeaux-700 pl-3">
                <p className="text-sm text-encre"><FormattedText text={d.content} /></p>
                {d.context && <p className="mt-1 text-xs text-encre-sourde"><FormattedText text={d.context} /></p>}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section eyebrow={`${actions.length} element(s)`} title="Actions">
        {actions.length === 0 ? (
          <EmptyRow label="Aucune action identifiee." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-liseret text-left">
                  <th className="py-2 pr-4 font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde">Action</th>
                  <th className="py-2 pr-4 font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde">Responsable</th>
                  <th className="py-2 font-donnees text-[11px] uppercase tracking-[0.1em] text-encre-sourde">Echeance</th>
                </tr>
              </thead>
              <tbody>
                {actions.map((a) => (
                  <tr key={a.id} className="border-b border-liseret last:border-b-0">
                    <td className="py-2.5 pr-4 text-encre-douce"><FormattedText text={a.content} /></td>
                    <td className="py-2.5 pr-4 text-encre-sourde">{a.responsible || '\u2014'}</td>
                    <td className="py-2.5 font-donnees text-xs text-encre-sourde">{a.deadline || '\u2014'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section eyebrow={`${questions.length} element(s)`} title="Questions ouvertes">
        {questions.length === 0 ? (
          <EmptyRow label="Aucune question restee sans reponse." />
        ) : (
          <ul className="flex flex-col gap-3">
            {questions.map((q) => (
              <li key={q.id} className="border-l-2 border-taupe-500 pl-3">
                <p className="text-sm text-encre"><FormattedText text={q.content} /></p>
                {q.context && <p className="mt-1 text-xs text-encre-sourde"><FormattedText text={q.context} /></p>}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section eyebrow={`${risks.length} element(s)`} title="Risques">
        {risks.length === 0 ? (
          <EmptyRow label="Aucun risque identifie." />
        ) : (
          <ul className="flex flex-col gap-3">
            {risks.map((r) => (
              <li key={r.id} className={`border-l-2 pl-3 ${severityTone(r.severity)}`}>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-encre"><FormattedText text={r.content} /></p>
                  {r.severity && (
                    <span className="font-donnees text-[10px] uppercase tracking-[0.08em] text-encre-sourde">
                      {r.severity}
                    </span>
                  )}
                </div>
                {r.mitigation && <p className="mt-1 text-xs text-encre-sourde">Mitigation : <FormattedText text={r.mitigation} /></p>}
              </li>
            ))}
          </ul>
        )}
      </Section>

      {summary.conclusion && (
        <Section eyebrow="Bilan" title="Conclusion">
          <p className="text-sm leading-relaxed text-encre-douce"><FormattedText text={summary.conclusion} /></p>
        </Section>
      )}
    </div>
  );
}
