import { NavLink } from "react-router-dom";
import type { ReportType } from "../../api/types";

const REPORT_TABS: { type: ReportType; label: string }[] = [
  { type: "executive", label: "Executive" },
  { type: "engineering", label: "Engineering" },
  { type: "cab", label: "CAB" },
];

export function ReportTabs({ caseId, activeType }: { caseId: string; activeType: ReportType }) {
  return (
    <div className="tabs" role="tablist" aria-label="Report types">
      {REPORT_TABS.map((tab) => (
        <NavLink
          key={tab.type}
          to={`/cases/${caseId}/reports/${tab.type}`}
          className={`tab${activeType === tab.type ? " active" : ""}`}
          role="tab"
          aria-selected={activeType === tab.type}
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
