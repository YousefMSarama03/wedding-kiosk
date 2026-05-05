import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getEvents, getEvent, createEvent, updateEvent, deleteEvent } from "../../services/api";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

const EVENT_TYPE_OPTIONS = [
  { value: "wedding", label: "Wedding" },
  { value: "palestinian_henna", label: "Palestinian Henna Party" },
  { value: "graduation", label: "Graduation" },
];

function EventFormModal({ event, onClose, onSaved }) {
  const [bride_name, setBrideName] = useState(event?.bride_name ?? "");
  const [groom_name, setGroomName] = useState(event?.groom_name ?? "");
  const [event_type, setEventType] = useState(event?.event_type ?? "wedding");
  const [wedding_date, setWeddingDate] = useState(event?.wedding_date ?? "");
  const [bride_image_file, setBrideImageFile] = useState(null);
  const [max_photos, setMaxPhotos] = useState(
    event?.max_photos != null && event?.max_photos !== "" ? String(event.max_photos) : ""
  );
  const brideImageUrl = event?.bride_image
    ? (typeof event.bride_image === "string" ? event.bride_image : event.bride_image?.url)
    : null;
  const [bride_image_preview, setBrideImagePreview] = useState(brideImageUrl || null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isEdit = !!event?.id;

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setBrideImageFile(file);
      setBrideImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const trimmedLimit = max_photos.trim();
    if (trimmedLimit !== "") {
      const n = parseInt(trimmedLimit, 10);
      if (Number.isNaN(n) || n < 1) {
        setError("Photo limit must be a whole number of at least 1, or leave blank for unlimited.");
        return;
      }
    }
    setSaving(true);
    try {
      const formData = new FormData();
      formData.append("bride_name", bride_name.trim());
      formData.append("groom_name", groom_name.trim());
      formData.append("event_type", event_type);
      formData.append("wedding_date", wedding_date);
      formData.append("max_photos", trimmedLimit === "" ? "" : String(parseInt(trimmedLimit, 10)));
      if (bride_image_file) formData.append("bride_image", bride_image_file);

      if (isEdit) {
        await updateEvent(event.id, formData);
      } else {
        await createEvent(formData);
      }
      onSaved();
      onClose();
    } catch (err) {
      const msg = err.response?.data
        ? typeof err.response.data === "object"
          ? err.response.data.bride_name?.[0] ||
            err.response.data.groom_name?.[0] ||
            err.response.data.wedding_date?.[0] ||
            err.response.data.max_photos?.[0] ||
            err.response.data.event ||
            JSON.stringify(err.response.data)
          : String(err.response.data)
        : err.message || "Failed to save";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: "rgba(0,0,0,0.7)" }}>
      <div
        className="w-full max-w-md rounded-2xl border border-white/20 p-6 shadow-xl"
        style={{ backgroundColor: "#141414" }}
      >
        <h2 className="text-xl font-semibold tracking-tight text-white">
          {isEdit ? "Edit event" : "Create event"}
        </h2>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Bride name</label>
            <input
              type="text"
              value={bride_name}
              onChange={(e) => setBrideName(e.target.value)}
              required
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
              placeholder="Bride name"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Groom name</label>
            <input
              type="text"
              value={groom_name}
              onChange={(e) => setGroomName(e.target.value)}
              required
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
              placeholder="Groom name"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Event type</label>
            <select
              value={event_type}
              onChange={(e) => setEventType(e.target.value)}
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            >
              {EVENT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Wedding date</label>
            <input
              type="date"
              value={wedding_date}
              onChange={(e) => setWeddingDate(e.target.value)}
              required
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Max guest photos</label>
            <input
              type="number"
              min={1}
              value={max_photos}
              onChange={(e) => setMaxPhotos(e.target.value)}
              placeholder="Unlimited"
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            />
            <p className="mt-1 text-xs text-white/50">
              Leave empty for no limit. Kiosk uploads count toward this cap.
            </p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-white/80">Bride photo (for AI)</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white/80 file:mr-2 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-1 file:text-sm file:text-white"
            />
            {bride_image_preview && (
              <img
                src={bride_image_preview}
                alt="Bride"
                className="mt-2 h-20 w-20 rounded-lg object-cover"
              />
            )}
          </div>
          {error && <p className="border border-white/20 bg-white/[0.04] px-3 py-2 text-sm text-white/90">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-white/30 py-2 text-sm font-medium text-white hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-xl bg-white py-2 text-sm font-semibold text-black hover:bg-white/90 disabled:opacity-50"
            >
              {saving ? "Saving…" : isEdit ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [modal, setModal] = useState(null); // "create" | { type: "edit", event }

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getEvents();
      setEvents(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete event "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await deleteEvent(id);
      setEvents((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || err.message || "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  const openEdit = async (ev) => {
    try {
      const full = await getEvent(ev.id);
      setModal({ type: "edit", event: full });
    } catch (err) {
      alert(err.message || "Failed to load event");
    }
  };

  const filtered = events.filter(
    (e) =>
      !search ||
      [e.bride_name, e.groom_name, e.wedding_date].some((v) =>
        String(v ?? "").toLowerCase().includes(search.toLowerCase())
      )
  );

  return (
    <>
      <Card>
        <CardHeader
          title="Events"
          subtitle="Manage wedding events"
          action={
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="search"
                placeholder="Search events…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
              />
              <button
                type="button"
                onClick={() => setModal("create")}
                className="rounded-xl bg-white px-4 py-1.5 text-sm font-semibold text-black hover:bg-white/90"
              >
                Create event
              </button>
            </div>
          }
        />
        <CardContent className="p-0">
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <div className="border border-white/20 bg-white/[0.03] p-5 text-sm text-white/90">{error}</div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon="📅"
              title={events.length === 0 ? "No events" : "No matching events"}
              description={events.length === 0 ? "Create an event to get started." : "Try a different search."}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/20 bg-white/5">
                    <th className="px-5 py-3 font-medium text-white/80">Event Name</th>
                    <th className="px-5 py-3 font-medium text-white/80">Bride Photo</th>
                    <th className="px-5 py-3 font-medium text-white/80">Type</th>
                    <th className="px-5 py-3 font-medium text-white/80">Date</th>
                    <th className="px-5 py-3 font-medium text-white/80">Photos</th>
                    <th className="px-5 py-3 font-medium text-white/80">Limit</th>
                    <th className="px-5 py-3 font-medium text-white/80">Status</th>
                    <th className="px-5 py-3 font-medium text-white/80">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((ev) => (
                    <tr key={ev.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="px-5 py-3 font-medium text-white">
                        {ev.bride_name} & {ev.groom_name}
                      </td>
                      <td className="px-5 py-3">
                        {ev.bride_image ? (
                          <span className="text-white" title="Has bride photo">✓</span>
                        ) : (
                          <span className="text-white/40">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-white/70">
                        {EVENT_TYPE_OPTIONS.find((opt) => opt.value === ev.event_type)?.label ?? "Wedding"}
                      </td>
                      <td className="px-5 py-3 text-white/70">{ev.wedding_date}</td>
                      <td className="px-5 py-3 text-white/70">{ev.photos?.length ?? 0}</td>
                      <td className="px-5 py-3 text-white/70">
                        {ev.max_photos != null ? ev.max_photos : "—"}
                      </td>
                      <td className="px-5 py-3">
                        <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/80">Active</span>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => openEdit(ev)}
                            className="text-white/80 hover:text-white underline"
                          >
                            Edit
                          </button>
                          <Link to={`/admin/gallery?event=${ev.id}`} className="text-white/80 hover:text-white underline">
                            Gallery
                          </Link>
                          <a href={`/?event=${ev.id}`} className="text-white/80 hover:text-white underline" target="_blank" rel="noopener noreferrer">
                            Kiosk
                          </a>
                          <button
                            type="button"
                            onClick={() => handleDelete(ev.id, `${ev.bride_name} & ${ev.groom_name}`)}
                            disabled={deletingId === ev.id}
                            className="text-white/60 underline hover:text-white disabled:opacity-50"
                          >
                            {deletingId === ev.id ? "…" : "Delete"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {modal === "create" && (
        <EventFormModal
          key="create-event"
          onClose={() => setModal(null)}
          onSaved={() => load()}
        />
      )}
      {modal?.type === "edit" && modal?.event && (
        <EventFormModal
          key={modal.event.id}
          event={modal.event}
          onClose={() => setModal(null)}
          onSaved={() => load()}
        />
      )}
    </>
  );
}
