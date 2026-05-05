import { useEffect, useState } from "react";
import { getPhotos, deletePhoto, reprocessPhoto } from "../../services/api";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

function photoUrl(photo, field = "guest_image") {
  const v = photo[field];
  if (!v) return null;
  return typeof v === "string" ? v : v.url ?? v;
}

export default function PhotosPage() {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [actionId, setActionId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPhotos();
      setPhotos(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load photos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this photo?")) return;
    setActionId(id);
    try {
      await deletePhoto(id);
      setPhotos((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || err.message || "Delete failed");
    } finally {
      setActionId(null);
    }
  };

  const handleReprocess = async (id) => {
    setActionId(id);
    try {
      await reprocessPhoto(id);
      await load();
    } catch (err) {
      alert(err.response?.data?.error || err.message || "Reprocess failed");
    } finally {
      setActionId(null);
    }
  };

  const filtered = photos.filter(
    (p) =>
      !search ||
      String(p.id).includes(search) ||
      String(p.status ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Card>
      <CardHeader
        title="Photos"
        subtitle="All kiosk photos"
        action={
          <input
            type="search"
            placeholder="Search by ID or status…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
          />
        }
      />
      <CardContent className="p-0">
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="border border-white/20 bg-white/[0.03] p-5 text-sm text-white/90">{error}</div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title={photos.length === 0 ? "No photos" : "No matching photos"}
            description="Photos will appear when guests use the kiosk."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/20 bg-white/5">
                  <th className="px-5 py-3 font-medium text-white/80">Photo</th>
                  <th className="px-5 py-3 font-medium text-white/80">Guest / Event</th>
                  <th className="px-5 py-3 font-medium text-white/80">Status</th>
                  <th className="px-5 py-3 font-medium text-white/80">AI Processed</th>
                  <th className="px-5 py-3 font-medium text-white/80">Created</th>
                  <th className="px-5 py-3 font-medium text-white/80">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => {
                  const guestUrl = photoUrl(p);
                  const generatedUrl = photoUrl(p, "generated_image");
                  return (
                    <tr key={p.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="px-5 py-3">
                        {guestUrl ? (
                          <img src={guestUrl} alt="" className="h-12 w-12 rounded-lg object-cover" />
                        ) : (
                          <div className="h-12 w-12 rounded-lg bg-white/10" />
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-white">Photo #{p.id}</span>
                        <span className="block text-xs text-white/60">Event {p.event ?? p.event_id ?? "—"}</span>
                      </td>
                      <td className="px-5 py-3 text-white/70">
                        {p.status ?? (generatedUrl ? "completed" : "pending")}
                      </td>
                      <td className="px-5 py-3">
                        {p.generated_image || generatedUrl ? (
                          <span className="text-white">Yes</span>
                        ) : (
                          <span className="text-white/40">No</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-white/70">
                        {p.created_at ? new Date(p.created_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex flex-wrap gap-2">
                          {generatedUrl && (
                            <a href={generatedUrl} download className="text-white/80 hover:text-white underline">Download</a>
                          )}
                          <button
                            type="button"
                            onClick={() => handleReprocess(p.id)}
                            disabled={actionId === p.id}
                            className="text-white/80 hover:text-white underline disabled:opacity-50"
                          >
                            {actionId === p.id ? "…" : "Reprocess AI"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(p.id)}
                            disabled={actionId === p.id}
                            className="text-white/50 underline hover:text-white disabled:opacity-50"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
