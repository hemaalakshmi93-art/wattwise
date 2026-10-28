import React, { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import { useAsync } from "./hooks.js";
import { Loading, ErrorBox } from "./components/ui.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Footprint from "./pages/Footprint.jsx";
import Missions from "./pages/Missions.jsx";
import Community from "./pages/Community.jsx";
import Solar from "./pages/Solar.jsx";
import Resources from "./pages/Resources.jsx";
import Onboarding from "./pages/Onboarding.jsx";

const PAGES = [
  { id: "dashboard", label: "Dashboard" },
  { id: "footprint", label: "My Footprint" },
  { id: "missions", label: "Daily Missions" },
  { id: "community", label: "Community" },
  { id: "solar", label: "Solar Advisor" },
  { id: "resources", label: "Resource Hub" },
];

const pageFromHash = () => {
  const id = window.location.hash.replace("#/", "");
  return PAGES.some((p) => p.id === id) ? id : "dashboard";
};

function Logo() {
  return (
    <div className="logo">
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
        <rect width="28" height="28" rx="8" fill="#1f5f3f" />
        <path d="M15.5 5 8 15h5l-1 8 8-11h-5z" fill="#dff0e6" />
      </svg>
      <span>WattWise</span>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState(pageFromHash());
  const [menuOpen, setMenuOpen] = useState(false);
  const [version, setVersion] = useState(0);
  const [userId, setUserId] = useState(() => Number(localStorage.getItem("wattwise_user")) || null);
  const [creating, setCreating] = useState(false);
  const users = useAsync(() => api.users(), [version]);

  useEffect(() => {
    const onHash = () => setPage(pageFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = useCallback((id) => {
    window.location.hash = `#/${id}`;
    setMenuOpen(false);
  }, []);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  const list = users.data ? users.data.users : [];
  const user = list.find((u) => u.id === userId) || (list.length && !creating ? list[0] : null);

  useEffect(() => {
    if (user && user.id !== userId) {
      setUserId(user.id);
      localStorage.setItem("wattwise_user", String(user.id));
    }
  }, [user, userId]);

  if (users.loading && !users.data) return <div className="boot"><Loading label="Starting WattWise" /></div>;
  if (users.error) return <div className="boot"><ErrorBox error={users.error} onRetry={users.reload} /></div>;

  if (!user || creating) {
    return (
      <div className="boot">
        <Logo />
        <Onboarding
          onCancel={user ? () => setCreating(false) : null}
          onCreated={(u) => {
            localStorage.setItem("wattwise_user", String(u.id));
            setUserId(u.id);
            setCreating(false);
            refresh();
            go("dashboard");
          }}
        />
      </div>
    );
  }

  const props = { user, version, refresh, go };
  const View = { dashboard: Dashboard, footprint: Footprint, missions: Missions,
    community: Community, solar: Solar, resources: Resources }[page];

  return (
    <div className="shell">
      <header className="topbar">
        <Logo />
        <button className="btn ghost" aria-expanded={menuOpen} aria-controls="nav"
          onClick={() => setMenuOpen((o) => !o)}>{menuOpen ? "Close" : "Menu"}</button>
      </header>

      <aside id="nav" className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="side-logo"><Logo /></div>
        <nav aria-label="Main">
          {PAGES.map((p) => (
            <a key={p.id} href={`#/${p.id}`} className={page === p.id ? "active" : ""}
              aria-current={page === p.id ? "page" : undefined} onClick={() => setMenuOpen(false)}>
              {p.label}
            </a>
          ))}
        </nav>
        <div className="side-foot">
          <label className="small muted" htmlFor="profile">Profile</label>
          <select id="profile" value={user.id} onChange={(e) => {
            const id = Number(e.target.value);
            setUserId(id);
            localStorage.setItem("wattwise_user", String(id));
            setMenuOpen(false);
          }}>
            {list.map((u) => <option key={u.id} value={u.id}>{u.name}{u.is_demo ? " (demo)" : ""}</option>)}
          </select>
          <button className="btn ghost" onClick={() => { setCreating(true); setMenuOpen(false); }}>New profile</button>
        </div>
      </aside>

      <main className="main">
        <View {...props} />
      </main>
    </div>
  );
}
