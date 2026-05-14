import { Routes, Route, Navigate } from "react-router-dom";
import KioskApp from "./pages/kiosk/KioskApp";
import KioskMode from "./components/kiosk/KioskMode";
import AdminLayout from "./layout/AdminLayout";
import AdminLoginPage from "./pages/admin/AdminLoginPage";
import AdminAuthGuard from "./components/admin/AdminAuthGuard";
import DashboardPage from "./pages/admin/DashboardPage";
import EventsPage from "./pages/admin/EventsPage";
import GuestsPage from "./pages/admin/GuestsPage";
import PhotosPage from "./pages/admin/PhotosPage";
import AIProcessingPage from "./pages/admin/AIProcessingPage";
import GalleryPage from "./pages/admin/GalleryPage";
import SettingsPage from "./pages/admin/SettingsPage";

const isDev = import.meta.env?.DEV === true;

function App() {
  return (
    <>
    <Routes>
      <Route path="/" element={<KioskMode><KioskApp /></KioskMode>} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route
        path="/admin"
        element={
          <AdminAuthGuard>
            <AdminLayout />
          </AdminAuthGuard>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="guests" element={<GuestsPage />} />
        <Route path="photos" element={<PhotosPage />} />
        <Route path="ai-processing" element={<AIProcessingPage />} />
        <Route path="gallery" element={<GalleryPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </>
  );
}

export default App;
