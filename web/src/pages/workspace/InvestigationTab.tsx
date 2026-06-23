import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { InvestigationData } from "../../api/types";
import { InvestigationTimeline } from "../../components/case/InvestigationTimeline";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingState } from "../../components/ui/LoadingState";
import { useAsync } from "../../hooks/useAsync";

export function InvestigationTab() {
  const { caseId = "" } = useParams();
  const { data: status, loading, error, reload } = useAsync(
    () => api.getInvestigationStatus(caseId),
    [caseId],
  );
  const [investigating, setInvestigating] = useState(false);
  const [investigateError, setInvestigateError] = useState("");
  const [result, setResult] = useState<InvestigationData | null>(null);

  async function runInvestigation() {
    setInvestigating(true);
    setInvestigateError("");
    try {
      const investigation = await api.investigateCase(caseId);
      setResult(investigation);
      reload();
    } catch (err) {
      setInvestigateError(err instanceof Error ? err.message : "Investigation failed");
    } finally {
      setInvestigating(false);
    }
  }

  if (loading) return <LoadingState message="Loading investigation status…" />;

  return (
    <div>
      <ErrorBanner message={error || investigateError} />
      {status && <InvestigationTimeline status={status} />}

      <Card title="Run Investigation Pipeline">
        <p className="metric-hint">
          Delegates to FastAPI — analyze, discover, quality, recommend, and generate
          advisory change package. No configuration changes are performed.
        </p>
        <div className="actions">
          <button className="btn" type="button" onClick={runInvestigation} disabled={investigating}>
            {investigating ? "Running pipeline…" : "Run Investigation"}
          </button>
          <button className="btn btn-secondary" type="button" onClick={reload}>
            Refresh Status
          </button>
        </div>
      </Card>

      {result && (
        <Card title="Pipeline Result">
          <div className="grid-2">
            <div>
              <strong>Top hypothesis</strong>
              <p>{result.analysis.top_hypothesis ?? "—"}</p>
            </div>
            <div>
              <strong>Confidence</strong>
              <p>{result.analysis.confidence ?? "—"}%</p>
            </div>
            <div>
              <strong>Quality score</strong>
              <p>{result.quality.overall_score}</p>
            </div>
            <div>
              <strong>Recommendation</strong>
              <p>{result.recommendation.top_recommendation ?? "—"}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
