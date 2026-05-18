/**
 * Front-end logging service for ai-wedding-kiosk.
 * No external dependencies. Supports DEBUG, INFO, WARN, ERROR;
 * colored console output, export to file, and sending critical logs to the server.
 *
 * Usage:
 *   import logger, { createLogger, loggedFetch, getLogs, exportToFile, setLevel, LOG_LEVELS } from "./logger";
 *   const log = createLogger("MyComponent");
 *   log.debug("detail", { foo: 1 });
 *   log.info("step done");
 *   log.warn("fallback used");
 *   log.error("failed", { err });
 *   const res = await loggedFetch(url, init, { component: "MyComponent", label: "POST /api/..." });
 *   setLevel(LOG_LEVELS.INFO);  // in production, reduce noise
 */

// --- Log levels (higher number = more severe) ---
export const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

const LEVEL_NAMES = ["DEBUG", "INFO", "WARN", "ERROR"];

// --- Environment ---
const isDev = typeof import.meta !== "undefined" && import.meta.env?.DEV === true;
const API_BASE_URL = typeof import.meta !== "undefined"
  ? import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : "https://YOUR_BACKEND_PUBLIC_URL.up.railway.app")
  : "https://YOUR_BACKEND_PUBLIC_URL.up.railway.app";

function resolveApiUrl(url) {
  if (typeof url !== "string") return url;
  return url.startsWith("/api/") ? `${API_BASE_URL}${url}` : url;
}

// --- Console styling (works in Chrome/Edge/Firefox) ---
const STYLES = {
  DEBUG: "color: #6b7280; font-weight: 500;",
  INFO: "color: #2563eb; font-weight: 600;",
  WARN: "color: #ea580c; font-weight: 600;",
  ERROR: "color: #dc2626; font-weight: 700;",
};

const ICONS = {
  DEBUG: "🔍",
  INFO: "ℹ️",
  WARN: "⚠️",
  ERROR: "❌",
};

// --- In-memory buffer for export and UI ---
const logBuffer = [];
const MAX_BUFFER = 500;

// --- Current log level (default: DEBUG in dev, INFO in prod) ---
let currentLevel = isDev ? LOG_LEVELS.DEBUG : LOG_LEVELS.INFO;

// --- Server endpoint for critical logs ---
const CLIENT_LOGS_URL = "/api/client-logs/";

/**
 * Set minimum log level. Messages below this level are not printed or stored.
 * @param {number} level - One of LOG_LEVELS.DEBUG, .INFO, .WARN, .ERROR
 */
export function setLevel(level) {
  currentLevel = level;
}

/**
 * Get current minimum log level.
 */
export function getLevel() {
  return currentLevel;
}

/**
 * Check if a level should be logged.
 */
function shouldLog(level) {
  return level >= currentLevel;
}

/**
 * Format a single log entry for buffer (no colors).
 */
function formatEntry(level, message, payload, component) {
  const name = LEVEL_NAMES[level] || "LOG";
  return {
    level: name,
    message,
    payload: payload !== undefined ? payload : null,
    component: component || null,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Append to buffer and trim if over limit.
 */
function appendToBuffer(entry) {
  logBuffer.push(entry);
  if (logBuffer.length > MAX_BUFFER) {
    logBuffer.shift();
  }
}

/**
 * Send a single log entry to the backend (for WARN/ERROR).
 * Fire-and-forget; does not throw.
 */
async function sendToBackend(entry) {
  try {
    const csrfMatch = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    const csrf = csrfMatch ? csrfMatch[1] : null;
    const res = await fetch(resolveApiUrl(CLIENT_LOGS_URL), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrf && { "X-CSRFToken": csrf }),
      },
      body: JSON.stringify(entry),
      credentials: "include",
    });
    if (!res.ok) {
      // Avoid recursive logging
      if (typeof console !== "undefined" && console.warn) {
        console.warn("[Logger] Failed to send log to server", res.status);
      }
    }
  } catch (_) {
    // Ignore network errors to avoid breaking the app
  }
}

/**
 * Core log function: console output, buffer, and optionally send to server.
 */
function log(level, message, payload = undefined, component = null) {
  if (!shouldLog(level)) return;

  const levelName = LEVEL_NAMES[level] || "LOG";
  const entry = formatEntry(level, message, payload, component);
  appendToBuffer(entry);

  // Console output with style
  const icon = ICONS[levelName] || "";
  const style = STYLES[levelName] || "";
  const prefix = component ? `[${component}]` : "[App]";
  const label = `${icon} ${levelName} ${prefix}`;

  if (typeof console !== "undefined") {
    if (payload !== undefined && payload !== null) {
      console.groupCollapsed?.(`%c${label} ${message}`, style);
      console.log(payload);
      console.groupEnd?.();
    } else {
      console.log(`%c${label} ${message}`, style);
    }
  }

  // Send WARN and ERROR to backend
  if (level >= LOG_LEVELS.WARN) {
    sendToBackend(entry);
  }
}

/**
 * Create a logger bound to a component name (for easier filtering).
 * @param {string} component - e.g. "KioskApp", "PhotoCreation"
 * @returns {{ debug, info, warn, error, timeStart, timeEnd }}
 */
export function createLogger(component) {
  return {
    debug: (msg, payload) => log(LOG_LEVELS.DEBUG, msg, payload, component),
    info: (msg, payload) => log(LOG_LEVELS.INFO, msg, payload, component),
    warn: (msg, payload) => log(LOG_LEVELS.WARN, msg, payload, component),
    error: (msg, payload) => log(LOG_LEVELS.ERROR, msg, payload, component),
    /**
     * Start a timer. Call timeEnd with the same key to log duration.
     */
    timeStart: (key) => {
      if (!shouldLog(LOG_LEVELS.DEBUG)) return;
      performance.mark?.(`logger-${component}-${key}-start`);
    },
    timeEnd: (key) => {
      if (!shouldLog(LOG_LEVELS.DEBUG)) return;
      try {
        performance.mark?.(`logger-${component}-${key}-end`);
        performance.measure?.(`logger-${component}-${key}`, `logger-${component}-${key}-start`, `logger-${component}-${key}-end`);
        const measure = performance.getEntriesByName?.(`logger-${component}-${key}`).pop();
        const ms = measure?.duration ?? 0;
        log(LOG_LEVELS.DEBUG, `⏱ ${key}`, { durationMs: Math.round(ms) }, component);
      } catch (_) {}
    },
  };
}

// --- Default app logger (no component name) ---
export const logger = createLogger("App");

/**
 * Get recent log entries (for UI or inspection).
 * @param {number} [limit=100]
 * @returns {Array<{ level, message, payload, component, timestamp }>}
 */
export function getLogs(limit = 100) {
  return logBuffer.slice(-limit);
}

/**
 * Clear in-memory log buffer.
 */
export function clearLogs() {
  logBuffer.length = 0;
}

/**
 * Export logs to a downloadable file (JSON array).
 * @param {string} [filename] - e.g. "kiosk-logs-2026-03-14.json"
 */
export function exportToFile(filename) {
  const name = filename || `kiosk-logs-${new Date().toISOString().slice(0, 10)}.json`;
  const blob = new Blob([JSON.stringify(logBuffer, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

// --- Fetch wrapper with timing and error logging ---

/**
 * Wrapped fetch that logs request start/end, duration, and errors.
 * Use this for critical API calls (e.g. process-ai) to get consistent logs.
 *
 * @param {string} url
 * @param {RequestInit} init
 * @param {{ component?: string, label?: string }} [options] - Optional label for logs
 * @returns {Promise<Response>}
 */
export async function loggedFetch(url, init = {}, options = {}) {
  const component = options.component || "API";
  const label = options.label || url;
  const start = performance.now();

  const logApi = createLogger(component);
  logApi.debug(`Request start: ${label}`, { url, method: init.method || "GET" });

  try {
    const requestUrl = resolveApiUrl(url);
    const requestInit = { credentials: "include", ...init };
    const res = await fetch(requestUrl, requestInit);
    const durationMs = Math.round(performance.now() - start);

    if (!res.ok) {
      logApi.error(`Request failed: ${label}`, {
        url,
        status: res.status,
        statusText: res.statusText,
        durationMs,
      });
    } else {
      logApi.debug(`Request OK: ${label}`, { status: res.status, durationMs });
    }

    return res;
  } catch (err) {
    const durationMs = Math.round(performance.now() - start);
    logApi.error(`Request error: ${label}`, {
      url,
      durationMs,
      error: err?.message ?? String(err),
    });
    throw err;
  }
}

/**
 * Log component load time. Returns a cleanup that logs time-on-screen on unmount.
 * For use with React: useEffect(() => { const cleanup = logComponentLifecycle("KioskApp"); return cleanup; }, []);
 * Or use the usePerformanceLog hook from hooks/usePerformanceLog.js.
 *
 * @param {string} componentName
 * @param {boolean} [enabled=true]
 * @returns {() => void} Cleanup to call on unmount
 */
export function logComponentLifecycle(componentName, enabled = isDev) {
  if (typeof window === "undefined" || !enabled) return () => {};
  const logApi = createLogger(componentName);
  const start = performance.now();
  logApi.debug("Component mounted");
  return () => {
    const durationMs = Math.round(performance.now() - start);
    logApi.debug("Component unmounted", { timeOnScreenMs: durationMs });
  };
}

// Re-export for convenience
export default logger;
