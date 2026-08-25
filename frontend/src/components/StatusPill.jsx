export default function StatusPill({ label, tone = 'border-liseret-clair text-encre-sourde', className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.06em] ${tone} ${className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {label}
    </span>
  );
}
