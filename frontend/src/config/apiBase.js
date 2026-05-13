/**
 * API base URL for production (absolute) vs local dev (same-origin relative).
 * Set VITE_API_URL in production when the browser talks to a different origin than the SPA
 * (e.g. https://api.example.com with no path, no trailing slash).
 */
export function getApiBase() {
  const raw = import.meta.env.VITE_API_URL;
  if (raw == null || String(raw).trim() === "") return "";
  return String(raw).trim().replace(/\/$/, "");
}

/** Prefix an API path (must start with /) with VITE_API_URL when set. */
export function apiPath(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = getApiBase();
  return base ? `${base}${p}` : p;
}
