import { useLocation, useNavigate } from "react-router-dom";
import { logoutAdmin } from "../services/api";
import BrandLogo from "../components/ui/BrandLogo";

const titles = {
  "/admin": "Overview",
  "/admin/events": "Events",
  "/admin/guests": "Guests",
  "/admin/photos": "Photos",
  "/admin/ai-processing": "Processing",
  "/admin/gallery": "Gallery",
  "/admin/settings": "Settings",
};

export default function Navbar({ onMenuClick }) {
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname;
  const title = titles[path] ?? "Admin";

  const handleLogout = async () => {
    try {
      await logoutAdmin();
    } catch (_) {}
    navigate("/admin/login", { replace: true });
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-white/10 bg-black px-4 lg:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="-ml-1 shrink-0 p-2 text-white/50 hover:bg-white/10 hover:text-white lg:hidden"
          aria-label="Open menu"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <BrandLogo className="h-10 shrink-0" alt="Jerusalem Studio" />
        <h1 className="min-w-0 truncate font-display text-lg font-medium tracking-editorial text-white">
          {title}
        </h1>
      </div>
      <button
        type="button"
        onClick={handleLogout}
        className="ml-3 shrink-0 border border-white/15 bg-transparent px-3 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white hover:text-black"
      >
        Sign out
      </button>
    </header>
  );
}
