export function Loader({ label = 'Chargement...' }) {
  return (
    <div className="flex items-center gap-3 py-8 text-sm text-encre-sourde">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-bordeaux-400 border-t-transparent" aria-hidden="true" />
      {label}
    </div>
  );
}

export function SkeletonLine({ className = '' }) {
  return <div className={`h-3 animate-pulse rounded-full bg-liseret ${className}`} />;
}

export function SkeletonBlock({ className = '' }) {
  return <div className={`animate-pulse rounded-2xl bg-liseret ${className}`} />;
}
