import { useAsync } from "../hooks/useAsync";
import { api } from "../api/client";
import { ErrorBanner } from "./ErrorBanner";
import { LoadingState } from "./LoadingState";

interface CaseSummaryProps {
  caseId: string;
}

export function CaseSummaryCard({ caseId }: CaseSummaryProps) {
  const { data, loading, error } = useAsync(() => api.getCase(caseId), [caseId]);

  if (loading) return <LoadingState message="Loading case…" />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div className="card">
      <h2>{data.case_id}</h2>
      <p>
        <strong>Playbook:</strong> {data.playbook_id}
      </p>
      <p>
        <strong>State:</strong> <span className="badge">{data.state}</span>
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
    </div>
  );
}
