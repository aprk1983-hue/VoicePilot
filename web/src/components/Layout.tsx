import { NavLink } from "react-router-dom";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <strong>VoicePilot Enterprise</strong>
          <span>Read-only investigation — advisory outputs only</span>
        </div>
        <nav className="app-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : undefined)}>
            Dashboard
          </NavLink>
          <NavLink to="/cases" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Cases
          </NavLink>
          <NavLink
            to="/cases/new"
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            New Case
          </NavLink>
          <NavLink
            to="/validation"
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            Validation
          </NavLink>
        </nav>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        VoicePilot never performs configuration changes. Evidence-only, deterministic,
        read-only investigation platform.
      </footer>
    </div>
  );
}
