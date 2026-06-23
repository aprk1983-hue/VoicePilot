import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CaseSummaryCard } from "../components/CaseSummaryCard";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingState } from "../components/LoadingState";
import { MarkdownViewer } from "../components/MarkdownViewer";
import { useAsync } from "../hooks/useAsync";

export function ChangePackageViewerPage() {
  const { caseId = "" } = useParams();
  const { data, loading, error } = useAsync(() => api.getChangePackage(caseId), [caseId]);

  return (
    <div>
      <h1 className="page-title">Change Package Viewer</h1>
      <ErrorBanner message={error} />
      <CaseSummaryCard caseId={caseId} />

      {loading ? (
        <LoadingState message="Loading change package…" />
      ) : data ? (
        <div className="card">
          <h2>{data.title}</h2>
          <p>
            <strong>Package ID:</strong> {data.package_id}
          </p>
          <p>
            <strong>Risk level:</strong>{" "}
            <span className="badge">{data.risk_level}</span>
          </p>
          <p className="stat-label">
            Advisory only — VoicePilot never performs configuration changes.
          </p>
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
