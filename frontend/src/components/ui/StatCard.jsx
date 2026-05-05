export default function StatCard({ title, value, icon, subtitle }) {
  return (
    <div className="border border-white/10 bg-black p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.04)_inset] transition-colors hover:border-white/15">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-2xs font-medium uppercase tracking-[0.16em] text-white/45">{title}</p>
          <p className="mt-2 font-display text-3xl font-medium tabular-nums tracking-tight text-white">
            {value}
          </p>
          {subtitle && <p className="mt-1 text-xs text-white/40">{subtitle}</p>}
        </div>
        {icon && (
          <div className="flex h-11 w-11 shrink-0 items-center justify-center border border-white/10 bg-white/[0.03] text-white">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
