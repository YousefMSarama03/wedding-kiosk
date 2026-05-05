/**
 * Optional development-only UI to view recent logs, export to file, and clear buffer.
 * Renders as a floating panel; only mount when import.meta.env.DEV is true.
 */

import { useState, useEffect } from "react";
import { getLogs, clearLogs, exportToFile } from "../../services/logger";

const LEVEL_COLORS = {
  DEBUG: "text-gray-400",
  INFO: "text-blue-400",
  WARN: "text-amber-400",
  ERROR: "text-red-400",
};

export default function LogViewer() {
  const [logs, setLogs] = useState([]);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState(""); // "" = all, "DEBUG", "INFO", etc.

  const refresh = () => setLogs(getLogs(200));

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 1500);
    return () => clearInterval(t);
  }, []);

  const filtered = filter
    ? logs.filter((e) => e.level === filter)
    : logs;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col items-end gap-2">
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-lg bg-slate-800/90 px-3 py-2 text-xs font-medium text-white shadow-lg border border-slate-600 hover:bg-slate-700"
        title="Toggle log viewer"
      >
        📋 Logs ({logs.length})
      </button>

      {open && (
        <div
          className="w-[min(420px,95vw)] max-h-[70vh] rounded-xl bg-slate-900/95 border border-slate-600 shadow-2xl flex flex-col overflow-hidden"
          role="dialog"
          aria-label="Log viewer"
        >
          <div className="flex items-center justify-between gap-2 p-2 border-b border-slate-600 bg-slate-800/80">
            <span className="text-sm font-semibold text-white">Logs</span>
            <div className="flex items-center gap-1">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="rounded bg-slate-700 text-white text-xs px-2 py-1 border border-slate-600"
              >
                <option value="">All</option>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
              </select>
              <button
                type="button"
                onClick={() => {
                  exportToFile();
                }}
                className="rounded bg-slate-700 text-white text-xs px-2 py-1 border border-slate-600 hover:bg-slate-600"
              >
                Export
              </button>
              <button
                type="button"
                onClick={() => {
                  clearLogs();
                  refresh();
                }}
                className="rounded bg-slate-700 text-white text-xs px-2 py-1 border border-slate-600 hover:bg-slate-600"
              >
                Clear
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-2 font-mono text-xs space-y-1">
            {filtered.length === 0 ? (
              <p className="text-slate-500">No logs</p>
            ) : (
              [...filtered].reverse().map((entry, i) => (
                <div
                  key={`${entry.timestamp}-${i}`}
                  className={`rounded px-2 py-1 break-all ${LEVEL_COLORS[entry.level] ?? "text-slate-300"}`}
                >
                  <span className="opacity-70">{entry.timestamp?.slice(11, 23)}</span>{" "}
                  <span className="font-semibold">[{entry.level}]</span>{" "}
                  {entry.component && <span className="text-slate-400">[{entry.component}]</span>}{" "}
                  {entry.message}
                  {entry.payload != null && (
                    <pre className="mt-1 text-[10px] opacity-80 overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(entry.payload)}
                    </pre>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
