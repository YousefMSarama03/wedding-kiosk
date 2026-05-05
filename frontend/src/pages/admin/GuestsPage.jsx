import { useEffect, useState } from "react";
import { getGuests } from "../../services/api";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

export default function GuestsPage() {
  const [guests, setGuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [eventFilter, setEventFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getGuests();
        if (!cancelled) setGuests(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load guests");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = guests.filter((g) => {
    const matchSearch = !search || String(g.name ?? g.id).toLowerCase().includes(search.toLowerCase()) ||
      String(g.event_name ?? "").toLowerCase().includes(search.toLowerCase());
    const matchEvent = !eventFilter || String(g.event_id) === eventFilter;
    return matchSearch && matchEvent;
  });

  const eventOptions = [...new Set(guests.map((g) => g.event_id))].filter(Boolean);

  return (
    <Card>
      <CardHeader
        title="Guests"
        subtitle="Guest activity and photos"
        action={
          <div className="flex flex-wrap gap-2">
            <input
              type="search"
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            />
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            >
              <option value="">All events</option>
              {eventOptions.map((id) => (
                <option key={id} value={id}>Event {id}</option>
              ))}
            </select>
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
            icon="👥"
            title={guests.length === 0 ? "No guests" : "No matching guests"}
            description="Guest data appears when using the kiosk or when the guests API is connected."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/20 bg-white/5">
                  <th className="px-5 py-3 font-medium text-white/80">Guest Name</th>
                  <th className="px-5 py-3 font-medium text-white/80">Event</th>
                  <th className="px-5 py-3 font-medium text-white/80">Photo Preview</th>
                  <th className="px-5 py-3 font-medium text-white/80">Time</th>
                  <th className="px-5 py-3 font-medium text-white/80">Download</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((g) => (
                  <tr key={g.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="px-5 py-3 font-medium text-white">{g.name ?? `Guest ${g.id}`}</td>
                    <td className="px-5 py-3 text-white/70">{g.event_name ?? `Event ${g.event_id}`}</td>
                    <td className="px-5 py-3">
                      {g.photo_url ? (
                        <img src={g.photo_url} alt="" className="h-10 w-10 rounded-lg object-cover" />
                      ) : (
                        <span className="text-white/40">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-white/70">
                      {g.created_at ? new Date(g.created_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-5 py-3">
                      {g.photo_url ? (
                        <a href={g.photo_url} download className="text-white/80 hover:text-white underline">Download</a>
                      ) : (
                        <span className="text-white/40">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
