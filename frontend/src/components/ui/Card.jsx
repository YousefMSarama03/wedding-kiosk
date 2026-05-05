export function Card({ children, className = "" }) {
  return (
    <div
      className={`rounded-none border border-white/10 bg-black shadow-[0_0_0_1px_rgba(255,255,255,0.06)_inset] ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-white/10 px-5 py-4">
      <div className="min-w-0">
        <h2 className="font-display text-lg font-medium tracking-editorial text-white">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm font-normal leading-relaxed text-white/50">{subtitle}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function CardContent({ children, className = "" }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}
