/**
 * KioskApp.jsx
 *
 * Main kiosk container: holds screen state and renders the current step.
 * Flow: Login → Welcome → Camera → Preview → Style → Processing → QR Result.
 * Uses the frontend logger for flow steps, API timing, and errors.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import LoginPage from "../../components/kiosk/LoginPage";
import WelcomeScreen from "../../components/kiosk/WelcomeScreen";
import CameraCapture from "../../components/kiosk/CameraCapture";
import BrandLogo from "../../components/ui/BrandLogo";
import { createLogger, loggedFetch } from "../../services/logger";
import { usePerformanceLog } from "../../hooks/usePerformanceLog";

const log = createLogger("KioskApp");

const SCREENS = {
  LOGIN: "login",
  WELCOME: "welcome",
  CAMERA: "camera",
  PREVIEW: "preview",
  STYLE: "style",
  PROCESSING: "processing",
  QR: "qr",
};

/* Shared layout for placeholder screens: dark bg, card slide-up, minimal content */
function PlaceholderScreen({ title, subtitle, onNext, onBack, nextLabel = "Next" }) {
  return (
    <motion.div
      className="min-h-screen w-full flex items-center justify-center p-6"
      style={{ backgroundColor: "#0A0A0A" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <motion.div
        className="w-full max-w-lg rounded-2xl p-8 md:p-12 text-center"
        style={{ backgroundColor: "#141414" }}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="mb-4 flex justify-center">
          <BrandLogo className="h-16" alt="Jerusalem Studio" />
        </div>
        <h1 className="text-2xl md:text-3xl font-semibold text-white tracking-tight mb-2">
          {title}
        </h1>
        {subtitle && (
          <p className="text-white/60 text-base md:text-lg mb-8">{subtitle}</p>
        )}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {onBack && (
            <motion.button
              type="button"
              onClick={onBack}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl border border-white/30 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-white/30"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              Back
            </motion.button>
          )}
          {onNext && (
            <motion.button
              type="button"
              onClick={onNext}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl bg-white text-black font-semibold focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#141414]"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              {nextLabel}
            </motion.button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function KioskApp() {
  const [screen, setScreen] = useState(SCREENS.LOGIN);
  const [capturedImage, setCapturedImage] = useState(null); // data URL for preview & upload later
  const [selectedStyle, setSelectedStyle] = useState("cinematic");
  const [includeBride, setIncludeBride] = useState(true);
  const [eventId, setEventId] = useState(""); // chosen wedding event (id)
  const [photoId, setPhotoId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState("");
  const [qrData, setQrData] = useState(null); // { qr_code_url, download_url }
  const [events, setEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState("");
  const [flowError, setFlowError] = useState("");

  const handleLogin = () => setScreen(SCREENS.WELCOME);
  const handleWelcomeStart = () => setScreen(SCREENS.CAMERA);
  const goBack = (target) => () => setScreen(target);

  usePerformanceLog("KioskApp");

  // Load available events from the backend so the user can pick a real event.
  // This keeps the flow simple and avoids hardcoding event IDs.
  useEffect(() => {
    let cancelled = false;

    async function loadEvents() {
      setEventsLoading(true);
      setEventsError("");
      try {
        const res = await loggedFetch("/api/events/", { method: "GET" }, { component: "KioskApp", label: "GET /api/events/" });
        if (!res.ok) {
          throw new Error(await res.text());
        }
        const data = await res.json();
        if (cancelled) return;
        // Support both raw array and DRF paginated { results: [...] }.
        const list = Array.isArray(data) ? data : (data?.results ?? []);
        setEvents(list);
        log.info("Events loaded", { count: list.length });

        // If the user hasn't selected an event yet, default to the first event.
        if (!eventId && list.length > 0) {
          setEventId(String(list[0].id));
        }
      } catch (err) {
        log.error("Failed to load events", { error: err?.message });
        if (!cancelled) setEventsError("Could not load events. Make sure the backend is running (e.g. on port 8000). You can enter an event ID below if you know it.");
      } finally {
        if (!cancelled) setEventsLoading(false);
      }
    }

    // Only load events when entering the Style screen (not on every page).
    if (screen === SCREENS.STYLE) {
      loadEvents();
    }

    return () => {
      cancelled = true;
    };
  }, [screen]); // eslint-disable-line react-hooks/exhaustive-deps

  if (screen === SCREENS.LOGIN) {
    return <LoginPage onLogin={handleLogin} />;
  }

  if (screen === SCREENS.WELCOME) {
    return <WelcomeScreen onStart={handleWelcomeStart} />;
  }

  if (screen === SCREENS.CAMERA) {
    return (
      <CameraCapture
        onBack={goBack(SCREENS.WELCOME)}
        onCapture={(dataUrl) => {
          setCapturedImage(dataUrl);
          setScreen(SCREENS.PREVIEW);
        }}
      />
    );
  }

  if (screen === SCREENS.PREVIEW) {
    return (
      <motion.div
        className="min-h-screen w-full flex items-center justify-center p-4 sm:p-8"
        style={{ backgroundColor: "#0A0A0A" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <motion.div
          className="w-full max-w-2xl rounded-2xl p-4 sm:p-6 flex flex-col gap-4 sm:gap-6"
          style={{ backgroundColor: "#141414" }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="flex justify-center">
            <BrandLogo className="h-14" alt="Jerusalem Studio" />
          </div>
          <h1 className="text-lg sm:text-2xl font-semibold text-white tracking-tight">
            Preview
          </h1>
          <p className="text-white/60 text-sm sm:text-base">
            Review your captured photo. You can retake or continue to style selection.
          </p>
          <div className="w-full aspect-video bg-black/50 rounded-xl overflow-hidden flex items-center justify-center">
            {capturedImage ? (
              <img
                src={capturedImage}
                alt="Captured preview"
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-white/40 text-sm">No image captured yet.</span>
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-2">
            <motion.button
              type="button"
              onClick={() => setScreen(SCREENS.CAMERA)}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl border border-white/30 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-white/30"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              Retake
            </motion.button>
            <motion.button
              type="button"
              onClick={() => setScreen(SCREENS.STYLE)}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl bg:white bg-white text-black font-semibold focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#141414]"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              Use Photo
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    );
  }

  if (screen === SCREENS.STYLE) {
    return (
      <motion.div
        className="min-h-screen w-full flex items-center justify-center p-4 sm:p-8"
        style={{ backgroundColor: "#0A0A0A" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <motion.div
          className="w-full max-w-xl rounded-2xl p-4 sm:p-6 flex flex-col gap-4 sm:gap-6"
          style={{ backgroundColor: "#141414" }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="flex justify-center">
            <BrandLogo className="h-14" alt="Jerusalem Studio" />
          </div>
          <h1 className="text-lg sm:text-2xl font-semibold text-white tracking-tight">
            Style Selection
          </h1>
          <p className="text-white/60 text-sm sm:text-base">
            Choose a style, decide whether to include the bride, and confirm which event this photo belongs to.
          </p>

          {/* Event picker (loaded from backend), with manual ID fallback on error */}
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-white/70">Wedding Event</span>

            {eventsLoading ? (
              <p className="text-sm text-white/50">Loading events…</p>
            ) : eventsError ? (
              <>
                <p className="text-sm text-amber-400">{eventsError}</p>
                <input
                  type="number"
                  min="1"
                  value={eventId}
                  onChange={(e) => setEventId(e.target.value)}
                  placeholder="Enter event ID (e.g. 1)"
                  className="h-11 px-3 rounded-lg border border-white/20 bg-white/5 text-white placeholder:text-gray-500 text-sm focus:outline-none focus:border-white/40 focus:ring-1 focus:ring-white/30"
                />
                <p className="text-xs text-white/50">
                  Create an event at /admin/ first, then enter its ID here.
                </p>
              </>
            ) : (
              <select
                value={eventId}
                onChange={(e) => setEventId(e.target.value)}
                className="h-11 px-3 rounded-lg border border-white/20 bg-white/5 text-white text-sm appearance-none focus:outline-none focus:border-white/40 focus:ring-1 focus:ring-white/30"
                style={{ backgroundColor: "#141414", color: "#FFFFFF", colorScheme: "dark" }}
              >
                {events.length === 0 ? (
                  <option value="" style={{ backgroundColor: "#141414", color: "#FFFFFF" }}>
                    No events found — create one in admin
                  </option>
                ) : (
                  events.map((ev) => (
                    <option
                      key={ev.id}
                      value={String(ev.id)}
                      style={{ backgroundColor: "#141414", color: "#FFFFFF" }}
                    >
                      {ev.bride_name} & {ev.groom_name} — {ev.wedding_date}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>

          {!eventsError && eventId && (() => {
            const selectedEvent = events.find((e) => String(e.id) === eventId);
            if (!selectedEvent) return null;
            const photoCount = selectedEvent.photos?.length ?? 0;
            const cap = selectedEvent.max_photos;
            const hasCap = cap != null && cap !== "";
            const atLimit = hasCap && photoCount >= Number(cap);
            const bits = [];
            if (atLimit) {
              bits.push(
                <p key="limit" className="text-sm text-amber-400 bg-amber-400/10 rounded-lg px-3 py-2">
                  This event has reached its photo limit ({photoCount} / {cap}). Ask staff to raise the
                  limit in admin or choose another event.
                </p>
              );
            }
            if (includeBride && !selectedEvent.bride_image) {
              bits.push(
                <p key="bride" className="text-sm text-amber-400 bg-amber-400/10 rounded-lg px-3 py-2">
                  This event has no bride photo. Add one in the admin or select "User Only".
                </p>
              );
            }
            if (!atLimit && hasCap) {
              bits.push(
                <p key="count" className="text-xs text-white/50">
                  Photos for this event: {photoCount} / {cap}
                </p>
              );
            }
            if (bits.length === 0) return null;
            return <div className="flex flex-col gap-2">{bits}</div>;
          })()}

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-white/70">Style</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {["cinematic", "classic", "black-and-white"].map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => setSelectedStyle(style)}
                  className={`h-10 rounded-lg border text-sm capitalize ${
                    selectedStyle === style
                      ? "bg-white text-black border-white"
                      : "bg-white/5 text-white border-white/20"
                  }`}
                >
                  {style.replace("-", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-white/70">Final Image</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setIncludeBride(true)}
                className={`h-10 rounded-lg border text-sm ${
                  includeBride
                    ? "bg-white text-black border-white"
                    : "bg-white/5 text-white border-white/20"
                }`}
              >
                With Bride
              </button>
              <button
                type="button"
                onClick={() => setIncludeBride(false)}
                className={`h-10 rounded-lg border text-sm ${
                  !includeBride
                    ? "bg-white text-black border-white"
                    : "bg-white/5 text-white border-white/20"
                }`}
              >
                User Only
              </button>
            </div>
          </div>

          {flowError ? <p className="text-sm text-red-400">{flowError}</p> : null}

          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-2">
            <motion.button
              type="button"
              onClick={goBack(SCREENS.PREVIEW)}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl border border-white/30 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-white/30"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              Back
            </motion.button>
            <motion.button
              type="button"
              disabled={(() => {
                if (!eventId || eventsError) return false;
                const sel = events.find((e) => String(e.id) === eventId);
                const count = sel?.photos?.length ?? 0;
                const cap = sel?.max_photos;
                return cap != null && cap !== "" && count >= Number(cap);
              })()}
              onClick={async () => {
                setFlowError("");
                if (!capturedImage) {
                  setFlowError("No photo captured. Please go back and capture a photo.");
                  return;
                }
                if (!eventId) {
                  setFlowError("Please select an event.");
                  return;
                }
                const sel = events.find((e) => String(e.id) === eventId);
                const count = sel?.photos?.length ?? 0;
                const cap = sel?.max_photos;
                if (cap != null && cap !== "" && count >= Number(cap)) {
                  setFlowError(
                    `This event has reached its photo limit (${count} / ${cap}). Ask staff to adjust the limit or pick another event.`
                  );
                  return;
                }
                try {
                  setProcessing(true);
                  setProcessingMessage("");
                  log.info("Photo creation started", { eventId, style: selectedStyle, includeBride });
                  // 1) Upload captured image to backend (capture endpoint).
                  const captureRes = await loggedFetch(
                    "/api/photos/capture/",
                    {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        event_id: Number(eventId),
                        style: selectedStyle,
                        image_base64: capturedImage,
                      }),
                    },
                    { component: "KioskApp", label: "POST /api/photos/capture/" }
                  );
                  if (!captureRes.ok) {
                    let msg = "Upload failed. Please try again.";
                    try {
                      const text = await captureRes.text();
                      if (text) {
                        try {
                          const errBody = JSON.parse(text);
                          msg = errBody?.error || text;
                        } catch {
                          msg = text;
                        }
                      }
                    } catch (_) {}
                    log.error("Capture failed", { eventId, status: captureRes.status, msg });
                    setFlowError(msg || "We couldn’t save your photo. Please try again.");
                    setProcessing(false);
                    return;
                  }
                  const captureData = await captureRes.json();
                  const newPhotoId = captureData.photo_id;
                  setPhotoId(newPhotoId);
                  log.info("Capture OK", { photoId: newPhotoId });
                  setProcessingMessage("Creating your wedding photo… This usually takes a few seconds.");
                  setScreen(SCREENS.PROCESSING);

                  // 2) Trigger AI processing for that photo.
                  const processRes = await loggedFetch(
                    `/api/photos/${newPhotoId}/process-ai/`,
                    {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ style: selectedStyle, include_bride: includeBride }),
                    },
                    { component: "KioskApp", label: `POST /api/photos/${newPhotoId}/process-ai/` }
                  );
                  if (!processRes.ok) {
                    let msg = "AI processing failed. Please try again.";
                    try {
                      const text = await processRes.text();
                      if (text) {
                        try {
                          const errBody = JSON.parse(text);
                          msg = errBody?.error || (Array.isArray(errBody?.detail) ? errBody.detail[0] : errBody?.detail) || msg;
                        } catch {
                          msg = text;
                        }
                      }
                    } catch (_) {}
                    log.error("process-ai failed", { photoId: newPhotoId, status: processRes.status, msg });
                    setFlowError(
                      msg ||
                        "We couldn’t finish the AI photo right now. Please ask a staff member and try again."
                    );
                    setProcessingMessage("Something went wrong while creating your photo.");
                    setProcessing(false);
                    return;
                  }
                  log.info("process-ai OK", { photoId: newPhotoId });

                  // 3) Fetch QR code for the processed photo.
                  const qrRes = await loggedFetch(
                    `/api/photos/${newPhotoId}/qr/`,
                    { method: "GET" },
                    { component: "KioskApp", label: `GET /api/photos/${newPhotoId}/qr/` }
                  );
                  if (qrRes.ok) {
                    const qrJson = await qrRes.json();
                    setQrData(qrJson);
                    log.info("QR OK", { photoId: newPhotoId });
                  } else {
                    log.error("QR fetch failed", { photoId: newPhotoId, status: qrRes.status });
                    setFlowError(
                      "We created your photo, but the QR code is unavailable. Please ask a staff member to help you download it."
                    );
                  }
                  setProcessing(false);
                  setScreen(SCREENS.QR);
                } catch (err) {
                  log.error("Photo creation flow error", { error: err?.message });
                  setFlowError("Something went wrong while creating your photo. Please try again.");
                  setProcessingMessage("We hit a problem while processing your photo.");
                  setProcessing(false);
                }
              }}
              className="min-h-[52px] md:min-h-[56px] px-8 rounded-xl bg-white text-black font-semibold focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#141414] disabled:opacity-45 disabled:pointer-events-none"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
            >
              {processing ? "Processing..." : "Continue"}
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    );
  }

  if (screen === SCREENS.PROCESSING) {
    return (
      <PlaceholderScreen
        title="Processing"
        subtitle={processingMessage || "Creating your wedding photo… This usually takes a few seconds."}
        onBack={goBack(SCREENS.STYLE)}
      />
    );
  }

  if (screen === SCREENS.QR) {
    return (
      <motion.div
        className="min-h-screen w-full flex items-center justify-center p-4 sm:p-8"
        style={{ backgroundColor: "#0A0A0A" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <motion.div
          className="w-full max-w-xl rounded-2xl p-4 sm:p-6 flex flex-col gap-4 sm:gap-6 items-center text-center"
          style={{ backgroundColor: "#141414" }}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          <BrandLogo className="h-14" alt="Jerusalem Studio" />
          <h1 className="text-lg sm:text-2xl font-semibold text-white tracking-tight">
            Your Photo is Ready
          </h1>
          <p className="text-white/60 text-sm sm:text-base">
            Scan the QR code below to download your photo on your device. If something went wrong, please ask a staff member for help.
          </p>
          {qrData?.qr_code_url ? (
            <img
              src={qrData.qr_code_url}
              alt="QR code for download"
              className="w-40 h-40 sm:w-56 sm:h-56 bg-white rounded-lg p-2"
            />
          ) : (
            <span className="text-white/40 text-sm">QR code not available.</span>
          )}
          {qrData?.download_url && (
            <a
              href={qrData.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-white/80 underline"
            >
              Or tap here to open the download link
            </a>
          )}
          <motion.button
            type="button"
            onClick={() => {
              setCapturedImage(null);
              setSelectedStyle("cinematic");
              setIncludeBride(true);
              setPhotoId(null);
              setQrData(null);
              setFlowError("");
              setProcessing(false);
              setProcessingMessage("");
              setScreen(SCREENS.WELCOME);
            }}
            className="min-h-[48px] px-8 rounded-xl border border-white/30 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-white/30 mt-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
          >
            Start Over
          </motion.button>
        </motion.div>
      </motion.div>
    );
  }

  return null;
}
