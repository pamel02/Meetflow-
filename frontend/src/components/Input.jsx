export default function Input({ label, error, hint, className = '', id, ...rest }) {
  const inputId = id || rest.name;
  return (
    <label className="flex flex-col gap-2" htmlFor={inputId}>
      {label && (
        <span className="text-xs font-semibold text-encre-douce">{label}</span>
      )}
      <input
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? `${inputId}-description` : undefined}
        className={`rounded-xl border bg-white px-3.5 py-3 text-sm text-encre shadow-sm transition placeholder:text-taupe-500 focus:border-bordeaux-500 focus:ring-3 focus:ring-bordeaux-500/10 ${
          error ? 'border-red-300' : 'border-liseret'
        } ${className}`}
        {...rest}
      />
      {error && <span id={`${inputId}-description`} className="text-xs text-red-600">{error}</span>}
      {!error && hint && <span id={`${inputId}-description`} className="text-xs text-encre-sourde">{hint}</span>}
    </label>
  );
}
