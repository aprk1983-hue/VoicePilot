import { Link, NavLink, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { useTheme } from "../../context/ThemeProvider";

interface AppShellProps {
  children: React.ReactNode;
  title?: string;
}

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/cases", label: "Cases" },
  { to: "/cases/new", label: "New Case" },
  { to: "/validation", label: "Validation" },
];

export function AppShell({ children, title }: AppShellProps) {
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="shell">
      <aside className={`shell-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <strong>VoicePilot</strong>
          <span>Enterprise Investigation Platform</span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-readonly">
          Read-only advisory mode. VoicePilot never performs configuration changes or
          connects to live devices.
        </div>
      </aside>

      <div className="shell-main">
        <header className="shell-topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              type="button"
              className="btn btn-ghost btn-icon mobile-menu-btn"
              aria-label="Toggle menu"
              onClick={() => setSidebarOpen((open) => !open)}
            >
              ☰
            </button>
            {title && <h1 className="topbar-title">{title}</h1>}
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <Link className="btn btn-secondary btn-sm" to="/cases/new">
              + New Case
            </Link>
          </div>
        </header>

        <div className="shell-content">{children}</div>

        <footer className="shell-footer">
          Evidence-only · Deterministic · No configuration changes · No live connectivity
        </footer>
      </div>
    </div>
  );
}
