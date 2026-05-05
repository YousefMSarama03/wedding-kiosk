import { useEffect } from "react";
import { logComponentLifecycle } from "../services/logger";

/**
 * React hook: log component mount and unmount with load time / time-on-screen.
 * Only logs in development by default. Call once at top of component.
 *
 * @param {string} componentName - e.g. "KioskApp", "PhotoCreation"
 * @param {boolean} [enabled] - Defaults to import.meta.env.DEV
 */
export function usePerformanceLog(componentName, enabled = import.meta.env?.DEV) {
  useEffect(() => {
    if (!enabled) return;
    const cleanup = logComponentLifecycle(componentName, true);
    return cleanup;
  }, [componentName, enabled]);
}

export default usePerformanceLog;
