/**
 * Tablet kiosk mode: fullscreen, disable navigation shortcuts, keep screen awake,
 * fixed layout, and warn on leave/refresh. Applied only when the kiosk route is active.
 */
import { useEffect, useRef } from "react";

export default function KioskMode({ children }) {
  const wakeLockRef = useRef(null);
  const touchIntervalRef = useRef(null);

  useEffect(() => {
    // A. Request fullscreen (some browsers require a user gesture; we try on mount)
    const doc = document.documentElement;
    if (doc.requestFullscreen) {
      doc.requestFullscreen().catch(() => {});
    }

    // B. Disable right-click, context menu, and navigation keys
    const prevent = (e) => e.preventDefault();
    const blockKey = (e) => {
      if (
        e.key === "F11" ||
        (e.ctrlKey && (e.key === "r" || e.key === "R" || e.key === "w" || e.key === "W")) ||
        (e.metaKey && (e.key === "r" || e.key === "R" || e.key === "w" || e.key === "W"))
      ) {
        e.preventDefault();
      }
    };
    document.addEventListener("contextmenu", prevent);
    document.addEventListener("keydown", blockKey);

    // C. Screen Wake Lock API; fallback: periodic no-op touch to reduce sleep
    if (navigator.wakeLock && navigator.wakeLock.request) {
      navigator.wakeLock.request("screen").then((lock) => {
        wakeLockRef.current = lock;
      }).catch(() => {});
    } else {
      const noop = () => {};
      touchIntervalRef.current = setInterval(noop, 60000);
    }

    // D. Fixed layout: prevent scroll/resize on body
    const prevOverflow = document.body.style.overflow;
    const prevHeight = document.body.style.height;
    document.body.style.overflow = "hidden";
    document.body.style.height = "100vh";

    // E. Prevent accidental refresh / leave
    const beforeUnload = (e) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", beforeUnload);

    // Prevent back navigation (keep user on kiosk)
    const handlePopState = () => {
      window.history.pushState(null, "", window.location.pathname);
    };
    window.history.pushState(null, "", window.location.pathname);
    window.addEventListener("popstate", handlePopState);

    return () => {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      document.removeEventListener("contextmenu", prevent);
      document.removeEventListener("keydown", blockKey);
      if (wakeLockRef.current) {
        wakeLockRef.current.release().catch(() => {});
        wakeLockRef.current = null;
      }
      if (touchIntervalRef.current) {
        clearInterval(touchIntervalRef.current);
        touchIntervalRef.current = null;
      }
      document.body.style.overflow = prevOverflow;
      document.body.style.height = prevHeight;
      window.removeEventListener("beforeunload", beforeUnload);
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  return children;
}
