import { useEffect, useRef, useState } from 'react';
import FormattedText from './FormattedText';

const SUGGESTIONS = [
  { title: 'Résumer les échanges', detail: 'Faites ressortir les points essentiels', prompt: 'Résume les réunions de cette semaine.', icon: 'summary' },
  { title: 'Retrouver une décision', detail: 'Identifiez ce qui a été validé', prompt: 'Quelles sont les dernières décisions importantes ?', icon: 'decision' },
  { title: 'Suivre les actions', detail: 'Listez les responsables et échéances', prompt: 'Quelles actions sont encore à réaliser et par qui ?', icon: 'action' },
  { title: 'Analyser les tendances', detail: 'Repérez les sujets qui reviennent', prompt: 'Quels sujets reviennent le plus souvent ?', icon: 'trend' },
];

function SparkleIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M12 3c.45 4.36 2.64 6.55 7 7-4.36.45-6.55 2.64-7 7-.45-4.36-2.64-6.55-7-7 4.36-.45 6.55-2.64 7-7Z" />
      <path d="M19 16c.2 1.74 1.26 2.8 3 3-1.74.2-2.8 1.26-3 3-.2-1.74-1.26-2.8-3-3 1.74-.2 2.8-1.26 3-3Z" />
    </svg>
  );
}

function SuggestionIcon({ type }) {
  const paths = {
    summary: <><path d="M7 7h10M7 12h7M7 17h5" /><path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /></>,
    decision: <><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.3 2.3 4.9-5" /></>,
    action: <><path d="M9 11 12 14 22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></>,
    trend: <><path d="m3 17 6-6 4 4 8-9" /><path d="M15 6h6v6" /></>,
  };
  return <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">{paths[type]}</svg>;
}

export default function ChatBox({ onAsk, scopeLabel, placeholder = 'Posez une question sur vos réunions…' }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const textAreaRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const textarea = textAreaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`;
  }, [input]);

  const send = async (question) => {
    const value = (question ?? input).trim();
    if (!value || loading) return;
    setInput('');
    setMessages((current) => [...current, { role: 'user', text: value }]);
    setLoading(true);

    try {
      const data = await onAsk(value);
      setMessages((current) => [...current, { role: 'assistant', text: data.answer, sources: data.sources }]);
    } catch (error) {
      setMessages((current) => [...current, {
        role: 'assistant',
        text: error.message || 'Une erreur est survenue pendant la génération de la réponse.',
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <section className="relative flex min-h-0 flex-1 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        {!hasMessages ? (
          <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-5 pb-28 pt-10 sm:px-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-bordeaux-700 text-white shadow-[0_12px_30px_rgba(38,59,216,0.22)]">
              <SparkleIcon className="h-7 w-7" />
            </div>
            <p className="mt-6 text-xs font-semibold uppercase tracking-[0.16em] text-bordeaux-600">Mémoire d’entreprise</p>
            <h2 className="mt-2 text-center text-2xl font-bold tracking-[-0.035em] text-encre sm:text-3xl">Que souhaitez-vous retrouver ?</h2>
            <p className="mt-3 max-w-xl text-center text-sm leading-6 text-encre-sourde">
              Explorez vos réunions, décisions et actions avec des réponses fondées sur vos transcriptions.
            </p>

            <div className="mt-8 grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion.title}
                  type="button"
                  onClick={() => send(suggestion.prompt)}
                  className="group flex min-h-24 items-start gap-3 rounded-2xl border border-liseret bg-white p-4 text-left shadow-[0_4px_16px_rgba(16,24,40,0.035)] transition duration-200 hover:-translate-y-0.5 hover:border-bordeaux-400 hover:shadow-[0_10px_28px_rgba(38,59,216,0.09)]"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface-haute text-encre-sourde transition group-hover:bg-bordeaux-500/10 group-hover:text-bordeaux-700">
                    <SuggestionIcon type={suggestion.icon} />
                  </span>
                  <span className="min-w-0 pt-0.5">
                    <span className="block text-sm font-semibold text-encre">{suggestion.title}</span>
                    <span className="mt-1 block text-xs leading-5 text-encre-sourde">{suggestion.detail}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto w-full max-w-3xl px-4 pb-40 pt-8 sm:px-8">
            <div className="space-y-8">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`flex gap-3 sm:gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {message.role === 'assistant' && (
                    <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${message.error ? 'bg-red-50 text-red-600' : 'bg-bordeaux-700 text-white'}`}>
                      <SparkleIcon className="h-4 w-4" />
                    </span>
                  )}
                  <div className={message.role === 'user'
                    ? 'max-w-[85%] rounded-3xl rounded-br-lg bg-surface-haute px-5 py-3 text-sm leading-6 text-encre sm:max-w-[75%]'
                    : `min-w-0 flex-1 pt-1 text-sm leading-7 ${message.error ? 'text-red-700' : 'text-encre-douce'}`
                  }>
                    <FormattedText text={message.text} />
                    {message.sources?.length > 0 && (
                      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-liseret pt-3">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-encre-sourde">Sources</span>
                        {message.sources.map((source) => (
                          <span key={source} className="rounded-full border border-liseret bg-fond-doux px-2.5 py-1 font-donnees text-[10px] text-encre-sourde">Réunion {source}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-4">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-bordeaux-700 text-white"><SparkleIcon className="h-4 w-4" /></span>
                  <div className="flex items-center gap-1.5" aria-label="L’assistant prépare sa réponse">
                    {[0, 1, 2].map((dot) => <span key={dot} className="h-1.5 w-1.5 animate-pulse rounded-full bg-taupe-500" style={{ animationDelay: `${dot * 160}ms` }} />)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 bg-gradient-to-t from-white via-white/95 to-transparent px-4 pb-4 pt-12 sm:px-8 sm:pb-6">
        <form onSubmit={(event) => { event.preventDefault(); send(); }} className="pointer-events-auto mx-auto w-full max-w-3xl">
          <div className="flex items-end gap-2 rounded-[26px] border border-liseret-clair bg-white p-2 pl-5 shadow-[0_12px_40px_rgba(16,24,40,0.12)] transition focus-within:border-bordeaux-400 focus-within:shadow-[0_14px_44px_rgba(38,59,216,0.13)]">
            <textarea
              ref={textAreaRef}
              value={input}
              rows={1}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  send();
                }
              }}
              placeholder={placeholder}
              className="max-h-36 min-h-11 flex-1 resize-none bg-transparent py-3 text-sm leading-5 text-encre outline-none placeholder:text-taupe-500"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              aria-label="Envoyer la question"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-bordeaux-700 text-white shadow-sm transition hover:bg-bordeaux-800 disabled:cursor-not-allowed disabled:bg-surface-haute disabled:text-taupe-400"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="m5 12 7-7 7 7M12 19V5" /></svg>
            </button>
          </div>
          <p className="mt-2 truncate px-3 text-center text-[10px] text-encre-sourde">Réponses générées à partir de « {scopeLabel} » · Vérifiez les informations importantes.</p>
        </form>
      </div>
    </section>
  );
}
