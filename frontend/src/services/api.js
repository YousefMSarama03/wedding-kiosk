/**
 * Admin API service. Uses Axios for Django REST API.
 * Logs requests/responses and errors with timing via the logger service.
 */

import axios from "axios";
import { createLogger } from "./logger";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const apiLogger = createLogger("API");

/** Get CSRF token from cookie (Django sets csrftoken when using session/csrf). */
function getCsrfToken() {
  const name = "csrftoken";
  const match = document.cookie.match(new RegExp("(?:^|;\\s*)" + name + "=([^;]*)"));
  return match ? match[1] : null;
}

export const api = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Send CSRF token for state-changing requests so Django/DRF SessionAuthentication accepts them
api.interceptors.request.use((config) => {
  const token = getCsrfToken();
  if (token && !config.headers["X-CSRFToken"]) {
    config.headers["X-CSRFToken"] = token;
  }
  config.metadata = { startTime: performance.now(), url: config.url, method: config.method };
  return config;
});

// Log successful responses with duration
api.interceptors.response.use(
  (response) => {
    const durationMs = Math.round(performance.now() - (response.config.metadata?.startTime ?? 0));
    apiLogger.debug("Response OK", {
      url: response.config.url,
      method: response.config.method,
      status: response.status,
      durationMs,
    });
    return response;
  },
  (error) => {
    const meta = error.config?.metadata ?? {};
    const durationMs = Math.round(performance.now() - (meta.startTime ?? 0));
    apiLogger.error("Request failed", {
      url: meta.url ?? error.config?.url,
      method: meta.method ?? error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      durationMs,
      message: error.message,
    });
    return Promise.reject(error);
  }
);

// --- Auth (admin dashboard session login) ---
export async function loginAdmin({ username, password }) {
  const res = await api.post("/api/auth/login/", { username, password });
  return res.data;
}

export async function logoutAdmin() {
  await api.post("/api/auth/logout/");
}

/** Returns { user: { id, username } } or throws if not authenticated. */
export async function getAuthMe() {
  const res = await api.get("/api/auth/me/");
  return res.data;
}

/** Sets Django csrftoken cookie for session-authenticated POST/PATCH/DELETE. */
export async function ensureCsrfCookie() {
  await api.get("/api/auth/csrf/");
}

// --- Stats (GET /api/admin/stats/) ---
export async function getAdminStats() {
  const res = await api.get("/api/admin/stats/");
  return res.data;
}

// --- Admin: users (kiosk login) ---
export async function getUsers() {
  const res = await api.get("/api/admin/users/");
  return Array.isArray(res.data) ? res.data : [];
}

export async function createUser({ username, password, is_staff }) {
  await ensureCsrfCookie();
  await api.post("/api/admin/users/", { username, password, is_staff: !!is_staff });
}

// --- Events ---
export async function getEvents(params = {}) {
  const res = await api.get("/api/events/", { params });
  const data = res.data;
  return Array.isArray(data) ? data : data?.results ?? data?.data ?? [];
}

export async function getEvent(id) {
  const res = await api.get(`/api/events/${id}/`);
  return res.data;
}

/** Create event. Pass FormData with bride_name, groom_name, wedding_date, optional bride_image (file). */
export async function createEvent(formData) {
  const opts = formData instanceof FormData
    ? { headers: { "Content-Type": null } } // let browser set multipart/form-data with boundary
    : {};
  const res = await api.post("/api/events/", formData, opts);
  return res.data;
}

/** Update event. Pass FormData with any of bride_name, groom_name, wedding_date, bride_image (file). */
export async function updateEvent(id, formData) {
  const opts = formData instanceof FormData
    ? { headers: { "Content-Type": null } }
    : {};
  const res = await api.patch(`/api/events/${id}/`, formData, opts);
  return res.data;
}

export async function deleteEvent(id) {
  await api.delete(`/api/events/${id}/`);
}

// --- Photos ---
export async function getPhotos(params = {}) {
  const res = await api.get("/api/photos/", { params });
  const data = res.data;
  return Array.isArray(data) ? data : data?.results ?? data?.data ?? [];
}

export async function deletePhoto(id) {
  await ensureCsrfCookie();
  await api.delete(`/api/photos/${id}/`);
}

/** Long-running AI (rembg + merge + WaveSpeed/OpenAI); must exceed nginx proxy_read_timeout. */
const PROCESS_AI_TIMEOUT_MS = 300000;
const POLL_AI_INTERVAL_MS = 1500;

export async function getPhoto(id) {
  const res = await api.get(`/api/photos/${id}/`);
  return res.data;
}

/** When process-ai returns 202 (Celery), poll until the photo is completed or reset to pending. */
export async function waitForPhotoProcessed(photoId, options = {}) {
  const intervalMs = options.intervalMs ?? POLL_AI_INTERVAL_MS;
  const maxWaitMs = options.maxWaitMs ?? PROCESS_AI_TIMEOUT_MS;
  const start = performance.now();
  while (performance.now() - start < maxWaitMs) {
    const data = await getPhoto(photoId);
    if (data.status === "completed" && data.generated_image) return data;
    if (data.status === "pending") {
      throw new Error("AI processing failed or was reset.");
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("Timed out waiting for AI processing.");
}

export async function reprocessPhoto(id) {
  apiLogger.info("reprocessPhoto (process-ai) start", { photoId: id });
  const start = performance.now();
  try {
    const res = await api.post(`/api/photos/${id}/process-ai/`, {}, { timeout: 120000 });
    if (res.status === 202) {
      await waitForPhotoProcessed(id, { maxWaitMs: PROCESS_AI_TIMEOUT_MS });
    }
    apiLogger.info("reprocessPhoto OK", { photoId: id, durationMs: Math.round(performance.now() - start) });
  } catch (err) {
    apiLogger.error("reprocessPhoto failed", { photoId: id, durationMs: Math.round(performance.now() - start), error: err?.message });
    throw err;
  }
}

// --- Guests (derived from events + photos) ---
export async function getGuests(params = {}) {
  // Guests are currently represented implicitly as photos (one guest session per photo).
  // Derive a guest-like list by joining photos with their events.
  const [events, photos] = await Promise.all([getEvents(), getPhotos(params)]);
  const eventsById = new Map(events.map((e) => [e.id, e]));

  return photos.map((p) => {
    const ev = eventsById.get(p.event) || eventsById.get(p.event_id);
    const eventName =
      ev && ev.bride_name && ev.groom_name
        ? `${ev.bride_name} & ${ev.groom_name}`
        : ev
        ? `Event ${ev.id}`
        : p.event ?? p.event_id ?? null;

    const rawImage = p.generated_image || p.guest_image;
    const photoUrl =
      typeof rawImage === "string"
        ? rawImage
        : rawImage && typeof rawImage === "object"
        ? rawImage.url ?? null
        : null;

    return {
      id: p.id,
      name: `Guest ${p.id}`,
      event_id: p.event ?? p.event_id ?? null,
      event_name: eventName,
      photo_url: photoUrl,
      created_at: p.created_at ?? null,
    };
  });
}

// --- AI Jobs (derived from photos) ---
export async function getAIJobs(params = {}) {
  const photos = await getPhotos(params);
  return photos.map((p) => ({
    id: p.id,
    photo_id: p.id,
    status: p.status ?? (p.generated_image ? "completed" : "pending"),
    processing_time_seconds: null,
    created_at: p.created_at ?? null,
  }));
}

export async function getAIJobsStats() {
  const jobs = await getAIJobs();
  return {
    total: jobs.length,
    processing: jobs.filter((j) => j.status === "processing").length,
    completed: jobs.filter((j) => j.status === "completed").length,
    failed: jobs.filter((j) => j.status === "failed").length,
  };
}

// --- Gallery (use photos API; approve/hide/feature can be mocked) ---
export async function getGalleryPhotos(params = {}) {
  return getPhotos({ ...params, limit: 100 });
}

export async function approvePhoto(id) {
  try {
    await api.patch(`/api/photos/${id}/`, { approved: true });
  } catch (err) {
    if (err.response?.status === 404) return; // mock success
    throw err;
  }
}

export async function hidePhoto(id) {
  try {
    await api.patch(`/api/photos/${id}/`, { hidden: true });
  } catch (err) {
    if (err.response?.status === 404) return;
    throw err;
  }
}

export async function featurePhoto(id) {
  try {
    await api.patch(`/api/photos/${id}/`, { featured: true });
  } catch (err) {
    if (err.response?.status === 404) return;
    throw err;
  }
}
