import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getAdminStats, getEvents, getPhotos } from "../../services/api";
import StatCard from "../../components/ui/StatCard";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import { StatIconAi, StatIconEvents, StatIconGuests, StatIconPhotos } from "../../components/admin/AdminStatIcons";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [recentPhotos, setRecentPhotos] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statsRes, eventsRes, photosRes] = await Promise.all([
          getAdminStats(),
          getEvents(),
          getPhotos(),
        ]);
        if (cancelled) return;
        setStats(statsRes);
        const photos = Array.isArray(photosRes) ? photosRes : [];
        setRecentPhotos(photos.slice(0, 5));
        const act = statsRes?.photo_activity_by_event;
        if (Array.isArray(act) && act.length > 0) {
          setChartData(act.map((x) => ({ name: x.name, photos: x.photos })));
        } else {
          const events = Array.isArray(eventsRes) ? eventsRes : [];
          const byEvent = events.map((ev) => ({
            name: ev.bride_name && ev.groom_name ? `${ev.bride_name} & ${ev.groom_name}` : `Event ${ev.id}`,
            photos: ev.photos?.length ?? photos.filter((p) => p.event === ev.id || p.event_id === ev.id).length,
          }));
          setChartData(byEvent.length ? byEvent : [{ name: "No events", photos: 0 }]);
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) {
    return (
      <div className="border border-white/20 bg-white/[0.03] p-4 text-sm text-white/90">{error}</div>
    );
  }

  const s = stats || {};
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Events" value={s.total_events ?? 0} icon={<StatIconEvents />} />
        <StatCard title="Guests" value={s.total_guests ?? 0} icon={<StatIconGuests />} />
        <StatCard title="Photos" value={s.total_photos ?? 0} icon={<StatIconPhotos />} />
        <StatCard title="AI outputs" value={s.ai_generated_photos ?? 0} icon={<StatIconAi />} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Photo activity by event" subtitle="Photos per event" />
          <CardContent>
            {chartData.length && chartData[0].photos !== undefined ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "rgba(255,255,255,0.45)" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "rgba(255,255,255,0.45)" }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#000000",
                        border: "1px solid rgba(255,255,255,0.2)",
                        borderRadius: "0",
                      }}
                      labelStyle={{ color: "#fff" }}
                    />
                    <Bar dataKey="photos" fill="#ffffff" fillOpacity={0.92} radius={[0, 0, 0, 0]} maxBarSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState title="No event data" description="Create events and add photos to see activity." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Recent Photos" subtitle="Latest uploads" />
          <CardContent>
            {recentPhotos.length > 0 ? (
              <ul className="space-y-2">
                {recentPhotos.map((p) => (
                  <li
                    key={p.id}
                    className="flex items-center gap-3 border border-white/10 bg-white/[0.02] p-2.5"
                  >
                    {p.guest_image ? (
                      <img
                        src={typeof p.guest_image === "string" ? p.guest_image : p.guest_image?.url}
                        alt=""
                        className="h-10 w-10 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="h-10 w-10 bg-white/10" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-white">Photo #{p.id}</p>
                      <p className="text-xs text-white/60">{p.status ?? "—"}</p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No photos yet" description="Photos will appear here once guests use the kiosk." />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader title="Recent Guests" subtitle="Latest guest activity" />
        <CardContent>
          {(stats?.recent_guests?.length ?? 0) > 0 ? (
            <ul className="space-y-2">
              {stats.recent_guests.map((g) => (
                <li key={g.id} className="flex items-center justify-between border border-white/10 bg-white/[0.02] p-3">
                  <span className="font-medium text-white">{g.name ?? `Guest ${g.id}`}</span>
                  <span className="text-sm text-white/60">{g.event_name ?? "—"}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No recent guests" description="Guest activity will appear here." />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
