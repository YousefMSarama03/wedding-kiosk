import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { loginAdmin, getAuthMe, ensureCsrfCookie, registerStaffAccount } from "../../services/api";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [registerMode, setRegisterMode] = useState(false);
  const [regSignupKey, setRegSignupKey] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regPassword2, setRegPassword2] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/admin";

  useEffect(() => {
    getAuthMe()
      .then(() => navigate(from, { replace: true }))
      .catch(() => {})
      .finally(() => setCheckingAuth(false));
  }, [navigate, from]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginAdmin({ username, password });
      await ensureCsrfCookie().catch(() => {});
      navigate(from, { replace: true });
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.message ||
        "Login failed. Check username and password.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    if (regPassword !== regPassword2) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await registerStaffAccount({
        username: regUsername,
        password: regPassword,
        signup_key: regSignupKey,
      });
      await loginAdmin({ username: regUsername, password: regPassword });
      await ensureCsrfCookie().catch(() => {});
      navigate(from, { replace: true });
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.message ||
        "Could not create account.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="admin-root flex min-h-screen items-center justify-center bg-black">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="admin-root flex min-h-screen items-center justify-center bg-black px-4 py-12">
      <motion.div
        className="w-full max-w-[24rem]"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="mb-10 text-center">
          <p className="text-2xs font-medium uppercase tracking-[0.22em] text-white/40">Wedding Kiosk</p>
          <h1 className="mt-3 font-display text-3xl font-medium tracking-editorial text-white">
            {registerMode ? "Create staff account" : "Sign in"}
          </h1>
          <p className="mt-2 text-sm text-white/45">Staff console</p>
        </div>

        <div className="border border-white/15 bg-black p-8 shadow-[0_0_0_1px_rgba(255,255,255,0.04)_inset]">
          {!registerMode ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="username" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="Username"
                />
              </div>
              <div>
                <label htmlFor="password" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="••••••••"
                />
              </div>
              {error && (
                <p className="border border-white/20 bg-white/[0.04] px-3 py-2.5 text-sm text-white/90">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full border border-white bg-white py-2.5 text-sm font-semibold text-black transition-colors hover:bg-white/90 disabled:opacity-50"
              >
                {loading ? "Signing in…" : "Continue"}
              </button>
              <p className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setRegisterMode(true);
                    setError("");
                  }}
                  className="text-sm text-white/45 underline-offset-4 transition hover:text-white hover:underline"
                >
                  Create staff account
                </button>
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-5">
              <div>
                <label htmlFor="signup-key" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Registration key
                </label>
                <input
                  id="signup-key"
                  type="password"
                  value={regSignupKey}
                  onChange={(e) => setRegSignupKey(e.target.value)}
                  autoComplete="off"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="Provided by administrator"
                />
              </div>
              <div>
                <label htmlFor="reg-username" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Username
                </label>
                <input
                  id="reg-username"
                  type="text"
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  autoComplete="username"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="Choose a username"
                />
              </div>
              <div>
                <label htmlFor="reg-password" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Password
                </label>
                <input
                  id="reg-password"
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label htmlFor="reg-password2" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">
                  Confirm password
                </label>
                <input
                  id="reg-password2"
                  type="password"
                  value={regPassword2}
                  onChange={(e) => setRegPassword2(e.target.value)}
                  autoComplete="new-password"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="••••••••"
                />
              </div>
              {error && (
                <p className="border border-white/20 bg-white/[0.04] px-3 py-2.5 text-sm text-white/90">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full border border-white bg-white py-2.5 text-sm font-semibold text-black transition-colors hover:bg-white/90 disabled:opacity-50"
              >
                {loading ? "Creating…" : "Create account and sign in"}
              </button>
              <p className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setRegisterMode(false);
                    setError("");
                    setRegSignupKey("");
                    setRegUsername("");
                    setRegPassword("");
                    setRegPassword2("");
                  }}
                  className="text-sm text-white/45 underline-offset-4 transition hover:text-white hover:underline"
                >
                  Back to sign in
                </button>
              </p>
            </form>
          )}
        </div>
        <p className="mt-8 text-center">
          <a href="/" className="text-sm text-white/40 transition hover:text-white">
            ← Kiosk
          </a>
        </p>
      </motion.div>
    </div>
  );
}
