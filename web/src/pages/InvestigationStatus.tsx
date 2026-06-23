import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CaseSummaryCard } from "../components/CaseSummaryCard";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";

export function InvestigationStatusPage() {
  const { caseId = "" } = useParams();
  const { data, loading, error, reload } = useAsync(
    () => api.getInvestigationStatus(caseId),
    [caseId],
  );

  return (
    <div>
      <h1 className="page-title">Investigation Status</h1>
      <ErrorBanner message={error} />
      <CaseSummaryCard caseId={caseId} />

      {loading ? (
        <LoadingState message="Loading status…" />
      ) : data ? (
        <div className="card">
          <h2>Current Status</h2>
          <p>
            <strong>State:</strong> <span className="badge">{data.state}</span>
          </p>
          <p>
            <strong>Top hypothesis:</strong> {data.top_hypothesis ?? "—"}
          </p>
          <p>
            <strong>Confidence:</strong>{" "}
            {data.confidence != null ? `${data.confidence}%` : "—"}
          </p>
          <div className="grid-2">
            <div>
              <div className="stat-value">{data.finding_count}</div>
              <div className="stat-label">Findings</div>
            </div>
            <div>
              <div className="stat-value">{data.hypothesis_count}</div>
              <div className="stat-label">Hypotheses</div>
            </div>
            <div>
              <div className="stat-value">{data.recommendation_count}</div>
              <div className="stat-label">Recommendations</div>
            </div>
          </div>
          <div className="actions">
            <button type="button" className="btn btn-secondary" onClick={reload}>
              Refresh
            </button>
            <Link className="btn btn-secondary" to={`/cases/${caseId}`}>
              Back to Case
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
