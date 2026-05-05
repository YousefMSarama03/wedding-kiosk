/**
 * CameraCapture.jsx
 *
 * Fullscreen live preview and still capture for the kiosk flow.
 * - Timer: user picks 5s or 10s, then shutter starts countdown before capture.
 * - getUserMedia with facingMode preference where available.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import BrandLogo from "../ui/BrandLogo";

const TIMER_STORAGE_KEY = "kioskCaptureTimerSec";

function loadTimerPreference() {
  try {
    const s = sessionStorage.getItem(TIMER_STORAGE_KEY);
    if (s === "5" || s === "10") return Number(s);
  } catch {
    /* ignore */
  }
  return 5;
}

export default function CameraCapture({ onCapture, onBack }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const [error, setError] = useState("");
  const [timerSeconds, setTimerSeconds] = useState(loadTimerPreference);
  const [countdown, setCountdown] = useState(null);

  const clearCountdownInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err) {
        console.error("Error accessing camera", err);
        if (err?.name === "NotAllowedError" || err?.name === "PermissionDeniedError") {
          setError(
            "Camera access was blocked. Please allow camera permissions and ask a staff member for help if this screen stays here."
          );
        } else if (err?.name === "NotFoundError" || err?.name === "DevicesNotFoundError") {
          setError("No camera was found on this device.");
        } else {
          setError("Unable to access the camera right now. Please ask a staff member for help.");
        }
      }
    }

    if (navigator.mediaDevices?.getUserMedia) {
      setupCamera();
    } else {
      setError("Camera is not supported in this browser.");
    }

    return () => {
      cancelled = true;
      clearCountdownInterval();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [clearCountdownInterval]);

  const performCapture = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
    onCapture?.(dataUrl);
  }, [onCapture]);

  const cancelCountdown = useCallback(() => {
    clearCountdownInterval();
    setCountdown(null);
  }, [clearCountdownInterval]);

  const handleBack = useCallback(() => {
    cancelCountdown();
    onBack?.();
  }, [cancelCountdown, onBack]);

  const startCountdownAndCapture = useCallback(() => {
    if (error || countdown !== null) return;

    let remaining = timerSeconds;
    setCountdown(remaining);

    intervalRef.current = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearCountdownInterval();
        setCountdown(null);
        performCapture();
      } else {
        setCountdown(remaining);
      }
    }, 1000);
  }, [error, countdown, timerSeconds, clearCountdownInterval, performCapture]);

  const setTimerAndPersist = (sec) => {
    setTimerSeconds(sec);
    try {
      sessionStorage.setItem(TIMER_STORAGE_KEY, String(sec));
    } catch {
      /* ignore */
    }
  };

  const isCountingDown = countdown !== null;

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col bg-black"
      style={{ minHeight: "100dvh", height: "100dvh" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="absolute inset-0 bg-black">
        {!error && (
          <video
            ref={videoRef}
            className="absolute inset-0 h-full w-full object-cover"
            muted
            playsInline
          />
        )}
      </div>

      <AnimatePresence>
        {isCountingDown && (
          <motion.div
            key="countdown-overlay"
            className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/45 backdrop-blur-[2px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <motion.span
              key={countdown}
              className="text-[min(28vw,9rem)] font-semibold tabular-nums text-white drop-shadow-[0_4px_24px_rgba(0,0,0,0.8)]"
              initial={{ scale: 0.72, opacity: 0.6 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 260, damping: 18 }}
            >
              {countdown}
            </motion.span>
            <p className="mt-4 text-sm text-white/80">Hold still…</p>
            <button
              type="button"
              onClick={cancelCountdown}
              className="mt-8 rounded-xl border border-white/35 bg-white/10 px-6 py-2.5 text-sm font-medium text-white backdrop-blur-sm hover:bg-white/20"
            >
              Cancel
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <header
        className="relative z-10 flex shrink-0 items-center justify-between px-4 pt-[max(1rem,env(safe-area-inset-top))] pb-3"
        style={{
          background: "linear-gradient(to bottom, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.35) 70%, transparent 100%)",
        }}
      >
        <div className="flex items-center gap-3">
          <BrandLogo className="h-9" alt="Jerusalem Studio" />
          <h1 className="text-lg font-semibold tracking-tight text-white sm:text-xl">Take a photo</h1>
        </div>
        {onBack && (
          <button
            type="button"
            onClick={handleBack}
            className="rounded-lg px-3 py-2 text-sm font-medium text-white/90 ring-1 ring-white/25 backdrop-blur-sm transition hover:bg-white/10 hover:text-white"
          >
            Back
          </button>
        )}
      </header>

      <div className="relative z-0 flex-1 min-h-0" aria-hidden />

      {error && (
        <div className="relative z-10 mx-4 mb-auto mt-4 rounded-xl bg-black/60 px-4 py-3 backdrop-blur-md">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      <footer
        className="relative z-10 flex shrink-0 flex-col items-center gap-5 px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-6"
        style={{
          background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 60%, transparent 100%)",
        }}
      >
        <div className="flex flex-col items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-white/50">Timer</span>
          <div
            className="flex rounded-xl bg-black/40 p-1 ring-1 ring-white/20 backdrop-blur-sm"
            role="group"
            aria-label="Countdown length before capture"
          >
            {[5, 10].map((sec) => (
              <button
                key={sec}
                type="button"
                disabled={!!error || isCountingDown}
                onClick={() => setTimerAndPersist(sec)}
                className={`min-w-[4.5rem] rounded-lg px-4 py-2 text-sm font-semibold transition disabled:opacity-40 ${
                  timerSeconds === sec
                    ? "bg-white text-black"
                    : "text-white/85 hover:bg-white/10"
                }`}
              >
                {sec}s
              </button>
            ))}
          </div>
        </div>

        <motion.button
          type="button"
          onClick={startCountdownAndCapture}
          disabled={!!error || isCountingDown}
          className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-white/90 bg-white/20 shadow-lg ring-4 ring-black/30 backdrop-blur-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:pointer-events-none disabled:opacity-35 sm:h-[4.5rem] sm:w-[4.5rem]"
          whileHover={error || isCountingDown ? {} : { scale: 1.06 }}
          whileTap={error || isCountingDown ? {} : { scale: 0.94 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
          aria-label={`Start ${timerSeconds} second countdown and capture`}
        >
          <span className="h-11 w-11 rounded-full bg-white sm:h-12 sm:w-12" />
        </motion.button>
      </footer>
    </motion.div>
  );
}
