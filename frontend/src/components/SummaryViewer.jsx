import Card, { CardHeader } from './Card';
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

export default function SummaryViewer({ report, pending }) {
  if (pending) {
    return (
      <p className="py-8 text-center text-sm text-encre-sourde">
        Le bilan IA est en cours de generation. Cette section se mettra a jour automatiquement.
      </p>
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
