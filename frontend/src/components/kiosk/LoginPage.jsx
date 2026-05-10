/**
 * LoginPage.jsx
 *
 * Kiosk login: dark theme (#0A0A0A / #141414), centered card,
 * username + password, touch-friendly inputs. Calls Django auth API;
 * on success calls onLogin(). Optional kiosk mode when VITE_KIOSK_SKIP_AUTH is set.
 */

import { useState } from "react";
import { motion } from "framer-motion";

const KIOSK_SKIP_AUTH = import.meta.env.VITE_KIOSK_SKIP_AUTH === "true";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const doLogin = async (user, pass) => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: user, password: pass }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        // Backend may use "error" or DRF-style "detail" (string or array)
        const msg =
          data?.error ||
          (Array.isArray(data?.detail) ? data.detail[0] : data?.detail) ||
          `Login failed (${res.status}). Please try again.`;
        setError(msg);
        setLoading(false);
        return;
      }
      onLogin?.(data);
    } catch (err) {
      console.error("Login request failed", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    doLogin(username, password);
  };

  const handleKioskMode = () => {
    doLogin("kiosk", "kiosk");
  };

  return (
    <motion.div
      className="min-h-screen w-full flex items-center justify-center p-6"
      style={{ backgroundColor: "#0A0A0A" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <motion.div
        className="w-full max-w-md rounded-2xl p-8 md:p-10"
        style={{ backgroundColor: "#141414" }}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
      >
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <h1 className="text-center text-2xl md:text-3xl font-semibold text-white tracking-tight">
            AI Wedding Kiosk
          </h1>
          <div className="flex flex-col gap-2">
            <label htmlFor="username" className="text-sm font-medium text-white/70">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              className="min-h-[48px] md:min-h-[52px] px-4 rounded-xl border border-white/20 bg-white/5 text-white placeholder:text-white/40 focus:outline-none focus:border-white/50 focus:ring-1 focus:ring-white/30 transition-all text-base"
              autoComplete="username"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-sm font-medium text-white/70">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="min-h-[48px] md:min-h-[52px] px-4 rounded-xl border border-white/20 bg-white/5 text-white placeholder:text-white/40 focus:outline-none focus:border-white/50 focus:ring-1 focus:ring-white/30 transition-all text-base"
              autoComplete="current-password"
              required
            />
          </div>
          <motion.button
            type="submit"
            disabled={loading}
            className="min-h-[52px] md:min-h-[56px] w-full rounded-xl bg-white text-black font-semibold text-base focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#141414] disabled:opacity-70 disabled:cursor-not-allowed"
            whileHover={!loading ? { scale: 1.02 } : undefined}
            whileTap={!loading ? { scale: 0.98 } : undefined}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
          >
            {loading ? "Signing in…" : "Login"}
          </motion.button>
          {error && (
            <p className="text-sm text-red-400 text-center" role="alert">
              {error}
            </p>
          )}
          {KIOSK_SKIP_AUTH && (
            <button
              type="button"
              onClick={handleKioskMode}
              disabled={loading}
              className="text-sm text-white/50 hover:text-white/70 underline disabled:opacity-50"
            >
              Continue as kiosk (no password)
            </button>
          )}
        </form>
      </motion.div>
    </motion.div>
  );
}
