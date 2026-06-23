import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CaseSummaryCard } from "../components/CaseSummaryCard";
import { ErrorBanner } from "../components/ErrorBanner";
import type { InvestigationData } from "../api/types";

export function CaseDetailPage() {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const [investigating, setInvestigating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<InvestigationData | null>(null);

  async function runInvestigation() {
    setInvestigating(true);
    setError("");
    try {
      const data = await api.investigateCase(caseId);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation failed");
    } finally {
      setInvestigating(false);
    }
  }

  async function deleteCase() {
    if (!window.confirm(`Delete case ${caseId}?`)) return;
    setDeleting(true);
    setError("");
    try {
      await api.deleteCase(caseId);
      navigate("/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Case Detail</h1>
      <ErrorBanner message={error} />
      <CaseSummaryCard caseId={caseId} />

      <div className="card">
        <h2>Actions</h2>
        <div className="actions">
          <Link className="btn btn-secondary" to={`/cases/${caseId}/evidence`}>
            Upload Evidence
          </Link>
          <Link className="btn btn-secondary" to={`/cases/${caseId}/status`}>
            Investigation Status
          </Link>
          <button className="btn" type="button" onClick={runInvestigation} disabled={investigating}>
            {investigating ? "Investigating…" : "Run Investigation"}
          </button>
          <Link className="btn btn-secondary" to={`/cases/${caseId}/reports/executive`}>
            Reports
          </Link>
          <Link className="btn btn-secondary" to={`/cases/${caseId}/change-package`}>
            Change Package
          </Link>
          <button
            className="btn btn-danger"
            type="button"
            onClick={deleteCase}
            disabled={deleting}
          >
            {deleting ? "Deleting…" : "Delete Case"}
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2>Investigation Result</h2>
          <p>
            <strong>Top hypothesis:</strong> {result.analysis.top_hypothesis ?? "—"}
          </p>
          <p>
            <strong>Confidence:</strong> {result.analysis.confidence ?? "—"}%
          </p>
          <p>
            <strong>Quality score:</strong> {result.quality.overall_score}
          </p>
          <p>
            <strong>Recommendation:</strong> {result.recommendation.top_recommendation ?? "—"}
          </p>
          <p>
            <strong>Change package:</strong> {result.change_package.title}
          </p>
        </div>
      )}
    </div>
  );
}
