export default function StatCard({ label, value, sub }) {
  return (
    <div className="rounded-2xl border border-liseret bg-surface px-5 py-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
      <p className="text-xs font-medium text-encre-sourde">{label}</p>
      <p className="mt-2 font-display text-3xl font-bold tracking-[-0.04em] text-encre">{value}</p>
      {sub && <p className="mt-1 text-xs text-encre-sourde">{sub}</p>}
    </div>
  );
}
