import { createContext, useCallback, useContext, useRef, useState } from 'react';

const ToastContext = createContext(null);
let idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    if (timers.current[id]) clearTimeout(timers.current[id]);
  }, []);

  const push = useCallback((message, tone = 'info', duration = 5000) => {
    const id = ++idCounter;
    setToasts((prev) => [...prev, { id, message, tone }]);
    timers.current[id] = setTimeout(() => dismiss(id), duration);
    return id;
  }, [dismiss]);

  const notify = {
    info: (msg) => push(msg, 'info'),
    error: (msg) => push(msg, 'error', 7000),
    success: (msg) => push(msg, 'success'),
  };

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            onClick={() => dismiss(t.id)}
            className={`cursor-pointer rounded-xl border bg-white px-4 py-3 text-sm shadow-[0_12px_30px_rgba(16,24,40,0.12)] ${
              t.tone === 'error'
                ? 'border-red-200 text-red-700'
                : t.tone === 'success'
                ? 'border-emerald-200 text-emerald-700'
                : 'border-liseret-clair text-encre-douce'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast doit etre utilise a l\'interieur de ToastProvider');
  return ctx;
}
