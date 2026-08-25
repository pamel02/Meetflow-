import { useEffect } from 'react';

export default function Modal({ open, onClose, title, children, footer, width = 'max-w-lg' }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-encre/35 px-4 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`w-full ${width} overflow-hidden rounded-2xl border border-white/70 bg-surface shadow-[0_24px_80px_rgba(16,24,40,0.2)]`}
      >
        <div className="flex items-center justify-between border-b border-liseret px-5 py-4">
          <h2 className="font-display text-lg font-semibold text-encre">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Fermer"
            className="rounded-lg border border-liseret px-2.5 py-1.5 text-xs text-encre-sourde hover:border-bordeaux-400 hover:text-bordeaux-700"
          >
            Fermer
          </button>
        </div>
        <div className="px-5 py-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-liseret px-5 py-4">{footer}</div>}
      </div>
    </div>
  );
}
