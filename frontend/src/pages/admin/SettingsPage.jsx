import { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { getUsers, createUser } from "../../services/api";

export default function SettingsPage() {
  const [branding, setBranding] = useState({ eventName: "", logoUrl: "" });
  const [templates, setTemplates] = useState({ selected: "classic" });
  const [styles, setStyles] = useState({ background: "elegant" });
  const [saved, setSaved] = useState(false);

  const [users, setUsers] = useState([]);
  const [userForm, setUserForm] = useState({ username: "", password: "", is_staff: false });
  const [userError, setUserError] = useState("");
  const [userSaving, setUserSaving] = useState(false);

  useEffect(() => {
    getUsers().then(setUsers).catch(() => setUsers([]));
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleCreateUser = async () => {
    setUserError("");
    setUserSaving(true);
    try {
      await createUser(userForm);
      setUserForm({ username: "", password: "", is_staff: false });
      const list = await getUsers();
      setUsers(list);
    } catch (err) {
      setUserError(err.response?.data?.error || err.message || "Failed to create user");
    } finally {
      setUserSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <Card>
        <CardHeader
          title="Kiosk users"
          subtitle="Create login accounts for the kiosk. No need to use Django admin."
        />
        <CardContent className="space-y-4">
          <div
            className="flex flex-wrap items-end gap-3"
            role="group"
            aria-label="Add kiosk user"
          >
            <div>
              <label className="mb-1 block text-xs font-medium text-white/60">Username</label>
              <input
                type="text"
                value={userForm.username}
                onChange={(e) => setUserForm((f) => ({ ...f, username: e.target.value }))}
                required
                className="border border-white/15 bg-black px-3 py-1.5 text-sm text-white placeholder:text-white/35 focus:border-white focus:outline-none"
                placeholder="Username"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-white/60">Password</label>
              <input
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm((f) => ({ ...f, password: e.target.value }))}
                required
                className="border border-white/15 bg-black px-3 py-1.5 text-sm text-white placeholder:text-white/35 focus:border-white focus:outline-none"
                placeholder="Password"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-white/70">
              <input
                type="checkbox"
                checked={userForm.is_staff}
                onChange={(e) => setUserForm((f) => ({ ...f, is_staff: e.target.checked }))}
                className="rounded border-white/30 bg-white/5 text-white focus:ring-white/30"
              />
              Staff
            </label>
            <button
              type="button"
              onClick={handleCreateUser}
              disabled={userSaving}
              className="rounded-xl bg-white px-3 py-1.5 text-sm font-semibold text-black hover:bg-white/90 disabled:opacity-50"
            >
              {userSaving ? "…" : "Add user"}
            </button>
          </div>
          {userError && (
            <p className="border border-white/20 bg-white/[0.04] px-3 py-2 text-sm text-white/90">{userError}</p>
          )}
          {users.length > 0 && (
            <ul className="mt-3 space-y-1 border border-white/10 bg-white/[0.02] p-3">
              {users.map((u) => (
                <li key={u.id} className="flex items-center justify-between text-sm text-white/80">
                  <span>{u.username}</span>
                  {u.is_staff && <span className="rounded bg-white/10 px-1.5 text-xs">Staff</span>}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader
          title="AI providers"
          subtitle="Replicate and optional OpenAI keys are set on the server only (.env / Docker)."
        />
        <CardContent className="space-y-4">
          <p className="max-w-xl text-sm text-white/60">
            Set <code className="text-white/80">REPLICATE_API_TOKEN</code> for InstantID wedding
            generation. Optional: <code className="text-white/80">REPLICATE_INSTANTID_MODEL</code> to
            override the default model version. For emergency legacy DALL-E only, set{" "}
            <code className="text-white/80">OPENAI_API_KEY</code> and{" "}
            <code className="text-white/80">KEEPSAKE_USE_OPENAI_LEGACY=true</code>.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Event Branding" subtitle="Customize kiosk appearance" />
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="eventName" className="mb-1 block text-sm font-medium text-white/80">
              Event Name
            </label>
            <input
              id="eventName"
              type="text"
              value={branding.eventName}
              onChange={(e) => setBranding((b) => ({ ...b, eventName: e.target.value }))}
              placeholder="Smith Wedding"
              className="w-full max-w-md rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            />
          </div>
          <div>
            <label htmlFor="logoUrl" className="mb-1 block text-sm font-medium text-white/80">
              Logo URL
            </label>
            <input
              id="logoUrl"
              type="url"
              value={branding.logoUrl}
              onChange={(e) => setBranding((b) => ({ ...b, logoUrl: e.target.value }))}
              placeholder="https://…"
              className="w-full max-w-md rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Wedding Templates" subtitle="Default style templates for AI" />
        <CardContent className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-white/80">Template</label>
            <select
              value={templates.selected}
              onChange={(e) => setTemplates((t) => ({ ...t, selected: e.target.value }))}
              className="rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            >
              <option value="classic">Classic</option>
              <option value="cinematic">Cinematic</option>
              <option value="black-and-white">Black & White</option>
              <option value="vintage">Vintage</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader title="Background Styles" subtitle="Scene styles for generated photos" />
        <CardContent className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-white/80">Default background</label>
            <select
              value={styles.background}
              onChange={(e) => setStyles((s) => ({ ...s, background: e.target.value }))}
              className="rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white focus:border-white/40 focus:outline-none focus:ring-1 focus:ring-white/30"
            >
              <option value="elegant">Elegant</option>
              <option value="garden">Garden</option>
              <option value="ballroom">Ballroom</option>
              <option value="outdoor">Outdoor</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          className="border border-white bg-white px-4 py-2 text-sm font-semibold text-black hover:bg-white/90 focus:outline-none focus:ring-1 focus:ring-white focus:ring-offset-2 focus:ring-offset-black"
        >
          Save settings
        </button>
        {saved && <span className="text-sm text-white/50">Saved.</span>}
      </div>
    </form>
  );
}
