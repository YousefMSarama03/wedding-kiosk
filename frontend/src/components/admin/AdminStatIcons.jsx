/** Compact icons for dashboard / stat cards */

export function StatIconEvents({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" d="M4 6h16M4 10h16M8 3v3M16 3v3" opacity="0.5" />
      <rect className="stroke-current" x="5" y="11" width="14" height="9" rx="1.5" strokeWidth="1.25" />
    </svg>
  );
}

export function StatIconGuests({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className="stroke-current" cx="9" cy="8" r="2.75" strokeWidth="1.25" />
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" d="M4 19v-1.5a4 4 0 014-4h2a4 4 0 014 4V19" />
      <circle className="stroke-current" cx="17" cy="9" r="2.25" strokeWidth="1.25" />
    </svg>
  );
}

export function StatIconPhotos({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect className="stroke-current" x="4" y="5" width="16" height="14" rx="2" strokeWidth="1.25" />
      <circle className="stroke-current" cx="9" cy="10" r="1.5" strokeWidth="1.25" />
      <path className="stroke-current" strokeWidth="1.25" strokeLinejoin="round" d="M4 17l4.5-4.5 3 3L16 12l4 5" />
    </svg>
  );
}

export function StatIconAi({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" d="M12 3l1.2 3.6L17 8l-3.8 1.4L12 13l-1.2-3.6L7 8l3.8-1.4L12 3zM6 16l.6 1.8 1.8.6-1.8.6L6 21l-.6-1.8-1.8-.6 1.8-.6L6 16zM17 14l.4 1.2 1.2.4-1.2.4L17 17l-.4-1.2-1.2-.4 1.2-.4L17 14z" />
    </svg>
  );
}

export function StatIconList({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" d="M8 7h12M8 12h12M8 17h12M4 7h.01M4 12h.01M4 17h.01" />
    </svg>
  );
}

export function StatIconHourglass({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" d="M8 3h8v3l-3 4 3 4v3H8v-3l3-4-3-4V3zM8 21h8" />
    </svg>
  );
}

export function StatIconCheck({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

export function StatIconAlert({ className = "h-6 w-6" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className="stroke-current" strokeWidth="1.25" strokeLinecap="round" d="M12 9v4M12 17h.01M10.3 4.3h3.4L21 18H3L10.3 4.3z" />
    </svg>
  );
}
