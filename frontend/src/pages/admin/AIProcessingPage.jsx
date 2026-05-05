import { useEffect, useState } from "react";
import { getAIJobs, getAIJobsStats, reprocessPhoto } from "../../services/api";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import StatCard from "../../components/ui/StatCard";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import { StatIconAlert, StatIconCheck, StatIconHourglass, StatIconList } from "../../components/admin/AdminStatIcons";

function statusClass(status) {
  if (status === "completed") return "border border-white bg-white text-black";
  if (status === "processing") return "border border-white/40 text-white";
  if (status === "failed") return "border border-white/25 text-white/70";
  return "border border-white/15 text-white/60";
}

export default function AIProcessingPage() {
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryingId, setRetryingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, jobsRes] = await Promise.all([getAIJobsStats(), getAIJobs()]);
      setStats(statsRes);
      setJobs(Array.isArray(jobsRes) ? jobsRes : []);
    } catch (err) {
      setError(err.message || "Failed to load AI jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRetry = async (job) => {
    const id = job.photo_id ?? job.id;
    setRetryingId(id);
    try {
      await reprocessPhoto(id);
      await load();
    } catch (err) {
      setError(err.message || "Retry failed");
    } finally {
      setRetryingId(null);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) {
    return (
      <div className="border border-white/20 bg-white/[0.03] p-4 text-sm text-white/90">{error}</div>
    );
  }

  const s = stats || { total: 0, processing: 0, completed: 0, failed: 0 };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Pipeline runs" value={s.total ?? 0} icon={<StatIconList />} />
        <StatCard title="Processing" value={s.processing ?? 0} icon={<StatIconHourglass />} />
        <StatCard title="Completed" value={s.completed ?? 0} icon={<StatIconCheck />} />
        <StatCard title="Failed" value={s.failed ?? 0} icon={<StatIconAlert />} />
      </div>

      <Card>
        <CardHeader
          title="AI Jobs"
          subtitle="Monitor and retry processing"
          action={
            <button
              type="button"
              onClick={load}
              className="border border-white/20 bg-transparent px-3 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white hover:text-black"
            >
              Refresh
            </button>
          }
        />
        <CardContent className="p-0">
          {jobs.length === 0 ? (
            <EmptyState title="No pipeline jobs" description="Runs appear when photos are sent for AI processing." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.02]">
                    <th className="px-5 py-3 text-2xs font-medium uppercase tracking-[0.12em] text-white/45">Photo</th>
                    <th className="px-5 py-3 text-2xs font-medium uppercase tracking-[0.12em] text-white/45">Status</th>
                    <th className="px-5 py-3 text-2xs font-medium uppercase tracking-[0.12em] text-white/45">Time</th>
                    <th className="px-5 py-3 text-2xs font-medium uppercase tracking-[0.12em] text-white/45">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => (
                    <tr key={j.id} className="border-b border-white/10 hover:bg-white/[0.02]">
                      <td className="px-5 py-3 font-mono text-white">#{j.photo_id ?? j.id}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-block px-2 py-0.5 text-xs font-medium capitalize ${statusClass(j.status)}`}>
                          {j.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-white/50">
                        {j.processing_time_seconds != null ? `${j.processing_time_seconds}s` : "—"}
                      </td>
                      <td className="px-5 py-3">
                        {(j.status === "failed" || j.status === "pending") && (
                          <button
                            type="button"
                            onClick={() => handleRetry(j)}
                            disabled={retryingId === (j.photo_id ?? j.id)}
                            className="border border-white bg-white px-2.5 py-1 text-xs font-semibold text-black hover:bg-white/90 disabled:opacity-50"
                          >
                            {retryingId === (j.photo_id ?? j.id) ? "…" : "Retry"}
                          </button>
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
    </div>
  );
}
