import { Link, useParams } from "react-router-dom";
import { reportEndpoint } from "../api/client";
import type { ReportType } from "../api/types";
import { CaseSummaryCard } from "../components/CaseSummaryCard";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingState } from "../components/LoadingState";
import { MarkdownViewer } from "../components/MarkdownViewer";
import { useAsync } from "../hooks/useAsync";

const REPORT_TABS: { type: ReportType; label: string }[] = [
  { type: "executive", label: "Executive" },
  { type: "engineering", label: "Engineering" },
  { type: "cab", label: "CAB" },
];

export function ReportViewerPage() {
  const { caseId = "", reportType = "executive" } = useParams();
  const activeType = (reportType as ReportType) || "executive";

  const { data, loading, error } = useAsync(
    () => reportEndpoint(caseId, activeType),
    [caseId, activeType],
  );

  return (
    <div>
      <h1 className="page-title">Report Viewer</h1>
      <ErrorBanner message={error} />
      <CaseSummaryCard caseId={caseId} />

      <div className="tabs">
        {REPORT_TABS.map((tab) => (
          <Link
            key={tab.type}
            className={`tab ${activeType === tab.type ? "active" : ""}`}
            to={`/cases/${caseId}/reports/${tab.type}`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {loading ? (
        <LoadingState message="Loading report…" />
      ) : data ? (
        <div className="card">
          <h2>{data.report_type} Report</h2>
          <MarkdownViewer content={data.markdown} />
          <div className="actions">
            <Link className="btn btn-secondary" to={`/cases/${caseId}`}>
              Back to Case
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
