import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { getAuthMe, logoutAdmin } from "../../services/api";
import LoadingSpinner from "../ui/LoadingSpinner";

/**
 * Admin routes: requires session + staff.
 */
export default function AdminAuthGuard({ children }) {
  const [status, setStatus] = useState("loading");
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    getAuthMe()
      .then((data) => {
        if (cancelled) return;
        if (!data?.user?.is_staff) setStatus("forbidden");
        else setStatus("authenticated");
      })
      .catch(() => {
        if (!cancelled) setStatus("unauthenticated");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <div className="admin-root flex min-h-screen items-center justify-center bg-black">
        <LoadingSpinner />
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  if (status === "forbidden") {
    return (
      <div className="admin-root flex min-h-screen flex-col items-center justify-center gap-6 bg-black px-6">
        <div className="max-w-md text-center">
          <p className="text-2xs font-medium uppercase tracking-[0.2em] text-white/40">Access</p>
          <h1 className="mt-2 font-display text-2xl font-medium text-white">Staff only</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/45">
            This account does not have access to the console. Use a staff account or ask an administrator.
          </p>
        </div>
        <button
          type="button"
          onClick={async () => {
            try {
              await logoutAdmin();
            } catch (_) {}
            window.location.assign("/admin/login");
          }}
          className="border border-white/20 bg-transparent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-white hover:text-black"
        >
          Back to sign in
        </button>
      </div>
    );
  }

  return children;
}
