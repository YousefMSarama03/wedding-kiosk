import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { ensureCsrfCookie } from "../services/api";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    ensureCsrfCookie().catch(() => {});
  }, []);

  return (
    <div className="admin-root min-h-screen bg-black font-sans text-white">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex min-h-screen min-h-[100dvh] flex-col lg:pl-[17rem]">
        <Navbar onMenuClick={() => setSidebarOpen((o) => !o)} />
        <main className="flex-1 px-4 pb-8 pt-4 lg:px-8 lg:pb-10 lg:pt-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
