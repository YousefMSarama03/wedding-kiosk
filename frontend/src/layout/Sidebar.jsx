import { NavLink } from "react-router-dom";
import {
  IconArrowLeft,
  IconCalendar,
  IconCamera,
  IconCpu,
  IconDashboard,
  IconGallery,
  IconSettings,
  IconUsers,
} from "../components/admin/AdminNavIcons";

const menuItems = [
  { path: "/admin", end: true, label: "Overview", Icon: IconDashboard },
  { path: "/admin/events", end: false, label: "Events", Icon: IconCalendar },
  { path: "/admin/guests", end: false, label: "Guests", Icon: IconUsers },
  { path: "/admin/photos", end: false, label: "Photos", Icon: IconCamera },
  { path: "/admin/ai-processing", end: false, label: "Processing", Icon: IconCpu },
  { path: "/admin/gallery", end: false, label: "Gallery", Icon: IconGallery },
  { path: "/admin/settings", end: false, label: "Settings", Icon: IconSettings },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/80 backdrop-blur-[2px] lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`fixed left-0 top-0 z-40 flex h-full w-[17rem] flex-col border-r border-white/10 bg-black transition-transform duration-200 ease-out ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <div className="flex h-14 shrink-0 items-center border-b border-white/10 px-5">
          <p className="font-display text-lg font-medium tracking-editorial text-white">Wedding Kiosk</p>
        </div>
        <nav className="flex flex-1 flex-col gap-px overflow-y-auto p-3" aria-label="Admin">
          {menuItems.map((item) => {
            const ItemIcon = item.Icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                onClick={() => onClose?.()}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 text-[0.9375rem] font-medium transition-colors ${
                    isActive
                      ? "bg-white text-black"
                      : "text-white/50 hover:bg-white/[0.06] hover:text-white"
                  }`
                }
              >
                <span className="flex w-9 shrink-0 justify-center">
                  <ItemIcon className="h-[1.1rem] w-[1.1rem]" />
                </span>
                <span className="tracking-tight">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-white/10 p-4">
          <a
            href="/"
            className="flex items-center justify-center gap-2 border border-white/15 bg-transparent px-3 py-2.5 text-sm font-medium text-white/60 transition-colors hover:border-white hover:bg-white hover:text-black"
          >
            <IconArrowLeft className="h-4 w-4" />
            Kiosk
          </a>
        </div>
      </aside>
    </>
  );
}
