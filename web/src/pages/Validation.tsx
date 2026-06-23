import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { SUPPORTED_PLAYBOOKS } from "../api/types";
import type { ValidationData } from "../api/types";
import { Card } from "../components/ui/Card";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { MetricCard } from "../components/ui/MetricCard";
import { Badge } from "../components/ui/Badge";

export function ValidationPage() {
  const [playbookId, setPlaybookId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ValidationData | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.validate(playbookId || null);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Validation Suite</h1>
        <p className="page-subtitle">Run deterministic scenario validation via the API</p>
      </header>
      <ErrorBanner message={error} />
      <Card>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="playbook">
              Playbook (optional)
            </label>
            <select
              id="playbook"
              className="form-select"
              value={playbookId}
              onChange={(event) => setPlaybookId(event.target.value)}
            >
              <option value="">All supported playbooks</option>
              {SUPPORTED_PLAYBOOKS.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Validating…" : "Run Validation"}
          </button>
        </form>
      </Card>
      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <div className="metrics-grid">
            <MetricCard label="Scenarios" value={result.total_scenarios} />
            <MetricCard label="Passed" value={result.passed_count} />
            <MetricCard label="Failed" value={result.failed_count} />
            <MetricCard label="Accuracy" value={`${result.accuracy_percent}%`} />
          </div>
          <Card>
            <p>
              <strong>Playbook:</strong> {result.playbook_id ?? "All playbooks"}
            </p>
            <p>
              <strong>Average confidence:</strong> {result.average_confidence.toFixed(1)}%
            </p>
            {result.failed_count === 0 ? (
              <Badge variant="success">All scenarios passed</Badge>
            ) : (
              <Badge variant="warning">Failures detected</Badge>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
