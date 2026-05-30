import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { loginAdmin, getAuthMe, ensureCsrfCookie, createUser } from "../../services/api";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [showSignup, setShowSignup] = useState(false);
  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirm, setSignupConfirm] = useState("");
  const [signupIsStaff, setSignupIsStaff] = useState(false);
  const [signupError, setSignupError] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/admin";

  useEffect(() => {
    getAuthMe()
      .then((data) => {
        if (data?.user?.is_staff) {
          navigate(from, { replace: true });
        }
      })
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

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    setSignupError("");
    if (!signupUsername || !signupPassword) {
      setSignupError("Username and password are required.");
      return;
    }
    if (signupPassword.length < 8) {
      setSignupError("Password must be at least 8 characters.");
      return;
    }
    if (signupPassword !== signupConfirm) {
      setSignupError("Passwords do not match.");
      return;
    }
    setSignupLoading(true);
    try {
      await createUser({ username: signupUsername, password: signupPassword, is_staff: signupIsStaff });
      // auto-login after creating account
      await loginAdmin({ username: signupUsername, password: signupPassword });
      await ensureCsrfCookie().catch(() => {});
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err.response?.data?.error || err.message || "Could not create account.";
      setSignupError(msg);
    } finally {
      setSignupLoading(false);
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
          <h1 className="mt-3 font-display text-3xl font-medium tracking-editorial text-white">Sign in</h1>
          <p className="mt-2 text-sm text-white/45">Staff console</p>
        </div>

        <div className="border border-white/15 bg-black p-8 shadow-[0_0_0_1px_rgba(255,255,255,0.04)_inset]">
          {!showSignup ? (
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
            </form>
          ) : (
            <form onSubmit={handleCreateAccount} className="space-y-5">
              <div>
                <label htmlFor="signup-username" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">Username</label>
                <input
                  id="signup-username"
                  type="text"
                  value={signupUsername}
                  onChange={(e) => setSignupUsername(e.target.value)}
                  autoComplete="username"
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="Username"
                />
              </div>
              <div>
                <label htmlFor="signup-password" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">Password</label>
                <input
                  id="signup-password"
                  type="password"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="At least 8 characters"
                />
              </div>
              <div>
                <label htmlFor="signup-confirm" className="mb-1.5 block text-2xs font-medium uppercase tracking-[0.14em] text-white/45">Confirm password</label>
                <input
                  id="signup-confirm"
                  type="password"
                  value={signupConfirm}
                  onChange={(e) => setSignupConfirm(e.target.value)}
                  required
                  className="w-full border border-white/15 bg-black px-3 py-2.5 text-white placeholder:text-white/30 focus:border-white focus:outline-none"
                  placeholder="Confirm password"
                />
              </div>
              <div className="flex items-center gap-2">
                <input id="signup-is-staff" type="checkbox" checked={signupIsStaff} onChange={(e) => setSignupIsStaff(e.target.checked)} className="h-4 w-4" />
                <label htmlFor="signup-is-staff" className="text-sm text-white/60">Create staff account</label>
              </div>
              {signupError && (
                <p className="border border-white/20 bg-white/[0.04] px-3 py-2.5 text-sm text-white/90">{signupError}</p>
              )}
              <button
                type="submit"
                disabled={signupLoading}
                className="w-full border border-white bg-white py-2.5 text-sm font-semibold text-black transition-colors hover:bg-white/90 disabled:opacity-50"
              >
                {signupLoading ? "Creating…" : "Create account"}
              </button>
            </form>
          )}
        </div>
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setShowSignup((s) => !s)}
            className="text-sm text-white/60 hover:text-white underline"
          >
            {showSignup ? "← Back to sign in" : "Create an account"}
          </button>
        </div>
        <p className="mt-4 text-center">
          <a href="/" className="text-sm text-white/40 transition hover:text-white">
            ← Kiosk
          </a>
        </p>
      </motion.div>
    </div>
  );
}
