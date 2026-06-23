import { NavLink } from "react-router-dom";

const TABS = [
  { slug: "", label: "Overview" },
  { slug: "evidence", label: "Evidence" },
  { slug: "investigation", label: "Investigation" },
  { slug: "reports", label: "Reports" },
  { slug: "change-package", label: "Change Package" },
] as const;

export function CaseWorkspaceNav({ caseId }: { caseId: string }) {
  return (
    <nav className="tabs" aria-label="Case workspace">
      {TABS.map((tab) => (
        <NavLink
          key={tab.slug || "overview"}
          to={tab.slug ? `/cases/${caseId}/${tab.slug}` : `/cases/${caseId}`}
          end={tab.slug === ""}
          className={({ isActive }) => `tab${isActive ? " active" : ""}`}
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
