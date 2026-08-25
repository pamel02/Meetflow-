export default function Card({ children, className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag className={`rounded-2xl border border-liseret bg-surface shadow-[0_1px_2px_rgba(16,24,40,0.03),0_10px_30px_rgba(16,24,40,0.035)] ${className}`} {...rest}>
      {children}
    </Tag>
  );
}

export function CardHeader({ eyebrow, title, action, className = '' }) {
  return (
    <div className={`flex items-start justify-between gap-4 border-b border-liseret px-5 py-4.5 ${className}`}>
      <div>
        {eyebrow && (
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-encre-sourde">{eyebrow}</p>
        )}
        {title && <h3 className="mt-1 font-display text-lg font-semibold text-encre">{title}</h3>}
      </div>
      {action}
    </div>
  );
}
