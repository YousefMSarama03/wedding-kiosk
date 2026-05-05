/** Minimal stroke icons for admin navigation — consistent weight, no emoji. */

const stroke = "stroke-current";

export function IconDashboard({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect className={stroke} x="3" y="3" width="7.5" height="7.5" rx="1.5" strokeWidth="1.5" />
      <rect className={stroke} x="13.5" y="3" width="7.5" height="7.5" rx="1.5" strokeWidth="1.5" />
      <rect className={stroke} x="3" y="13.5" width="7.5" height="7.5" rx="1.5" strokeWidth="1.5" />
      <rect className={stroke} x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5" strokeWidth="1.5" />
    </svg>
  );
}

export function IconCalendar({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect className={stroke} x="3.5" y="5" width="17" height="16" rx="2" strokeWidth="1.5" />
      <path className={stroke} strokeWidth="1.5" strokeLinecap="round" d="M3.5 10h17M8 3.5V7M16 3.5V7" />
    </svg>
  );
}

export function IconUsers({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className={stroke} cx="9" cy="8" r="3" strokeWidth="1.5" />
      <path className={stroke} strokeWidth="1.5" strokeLinecap="round" d="M3 20v-1a5 5 0 015-5h2a5 5 0 015 5v1M17 11h2a3 3 0 013 3v1" />
      <circle className={stroke} cx="17" cy="8" r="3" strokeWidth="1.5" />
    </svg>
  );
}

export function IconCamera({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className={stroke} strokeWidth="1.5" strokeLinejoin="round" d="M4 8h2l1.5-2h9L18 8h2a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2v-8a2 2 0 012-2z" />
      <circle className={stroke} cx="12" cy="14" r="3.5" strokeWidth="1.5" />
    </svg>
  );
}

export function IconCpu({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect className={stroke} x="7" y="7" width="10" height="10" rx="1.5" strokeWidth="1.5" />
      <path className={stroke} strokeWidth="1.5" strokeLinecap="round" d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4" />
    </svg>
  );
}

export function IconGallery({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect className={stroke} x="3" y="4" width="18" height="16" rx="2" strokeWidth="1.5" />
      <circle className={stroke} cx="8.5" cy="9.5" r="1.5" strokeWidth="1.5" />
      <path className={stroke} strokeWidth="1.5" strokeLinejoin="round" d="M21 15l-5-5-4 4-3-3-5 5" />
    </svg>
  );
}

export function IconSettings({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className={stroke} cx="12" cy="12" r="3" strokeWidth="1.5" />
      <path className={stroke} strokeWidth="1.5" strokeLinecap="round" d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

export function IconArrowLeft({ className = "h-4 w-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path className={stroke} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" d="M15 18l-6-6 6-6" />
    </svg>
  );
}
