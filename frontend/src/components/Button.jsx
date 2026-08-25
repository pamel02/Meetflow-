const VARIANTS = {
  primary: 'bg-bordeaux-700 border border-bordeaux-700 text-white shadow-[0_8px_20px_rgba(38,59,216,0.18)] hover:-translate-y-0.5 hover:bg-bordeaux-800 hover:shadow-[0_10px_24px_rgba(38,59,216,0.24)] disabled:bg-taupe-300 disabled:border-taupe-300 disabled:shadow-none',
  secondary: 'bg-white border border-liseret-clair text-encre-douce shadow-sm hover:border-bordeaux-400 hover:text-bordeaux-700 hover:bg-bordeaux-500/5',
  ghost: 'bg-transparent border border-transparent text-encre-sourde hover:text-encre hover:bg-surface-haute',
  danger: 'bg-white border border-red-200 text-red-600 hover:border-red-300 hover:bg-red-50',
  recording: 'bg-red-600 border border-red-600 text-white shadow-[0_10px_24px_rgba(220,38,38,0.2)] hover:bg-red-700 hover:-translate-y-0.5',
};

const SIZES = {
  sm: 'text-xs px-3.5 py-2',
  md: 'text-sm px-4.5 py-2.5',
  lg: 'text-sm px-6 py-3.5',
};

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  loading = false,
  type = 'button',
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-corps font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border border-current border-t-transparent" aria-hidden="true" />
      )}
      {children}
    </button>
  );
}
