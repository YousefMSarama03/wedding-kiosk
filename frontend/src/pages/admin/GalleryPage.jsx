import { useEffect, useState } from "react";
import { getGalleryPhotos } from "../../services/api";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

function photoUrl(p, field = "generated_image") {
  const v = p[field] ?? p.guest_image;
  if (!v) return null;
  return typeof v === "string" ? v : v.url ?? v;
}

export default function GalleryPage() {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [eventFilter, setEventFilter] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getGalleryPhotos();
      setPhotos(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load gallery");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = eventFilter
    ? photos.filter((p) => String(p.event ?? p.event_id) === eventFilter)
    : photos;

  const eventIds = [...new Set(photos.map((p) => p.event ?? p.event_id).filter(Boolean))];

  return (
    <Card>
      <CardHeader
        title="Live Gallery"
        subtitle="All generated photos from the kiosk"
        action={
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="border border-white/15 bg-black px-3 py-1.5 text-sm text-white focus:border-white focus:outline-none"
          >
            <option value="">All events</option>
            {eventIds.map((id) => (
              <option key={id} value={id}>
                Event {id}
              </option>
            ))}
          </select>
        }
      />
      <CardContent>
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="border border-white/20 bg-white/[0.03] p-4 text-sm text-white/90">{error}</div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title={photos.length === 0 ? "No photos in gallery" : "No photos for this event"}
            description="Photos appear here after guests use the kiosk and AI processing completes."
          />
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
            {filtered.map((p) => {
              const url = photoUrl(p) || photoUrl(p, "guest_image");
              return (
                <div
                  key={p.id}
                  className="relative overflow-hidden border border-white/10 bg-white/[0.02]"
                >
                  {url ? (
                    <img src={url} alt="" className="aspect-square w-full object-cover" />
                  ) : (
                    <div className="aspect-square w-full bg-white/10" />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
