export default function EmptyState({ icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center border border-dashed border-white/15 bg-white/[0.02] px-6 py-14 text-center">
      {icon != null && icon !== false && (
        <span
          className="flex h-11 w-11 items-center justify-center border border-white/10 bg-black text-sm text-white/50"
          aria-hidden
        >
          {icon}
        </span>
      )}
      <h3 className="mt-4 font-display text-base font-medium tracking-editorial text-white">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-pretty text-sm leading-relaxed text-white/45">{description}</p>
      )}
    </div>
  );
}
