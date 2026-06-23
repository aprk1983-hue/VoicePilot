import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { SUPPORTED_PLAYBOOKS } from "../api/types";
import type { ValidationData } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";

export function ValidationPage() {
  const [playbookId, setPlaybookId] = useState<string>("");
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
      <h1 className="page-title">Validation</h1>
      <ErrorBanner message={error} />

      <form className="card" onSubmit={handleSubmit}>
        <p className="stat-label">
          Run the deterministic validation suite against scenario packs. This may take a
          minute for all playbooks.
        </p>
        <div className="form-group">
          <label htmlFor="playbook">Playbook (optional)</label>
          <select
            id="playbook"
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
        <div className="actions">
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Validating…" : "Run Validation"}
          </button>
        </div>
      </form>

      {result && (
        <div className="card">
          <h2>Validation Summary</h2>
          <p>
            <strong>Playbook:</strong> {result.playbook_id ?? "All playbooks"}
          </p>
          <div className="grid-2">
            <div>
              <div className="stat-value">{result.total_scenarios}</div>
              <div className="stat-label">Total scenarios</div>
            </div>
            <div>
              <div className="stat-value">{result.passed_count}</div>
              <div className="stat-label">Passed</div>
            </div>
            <div>
              <div className="stat-value">{result.failed_count}</div>
              <div className="stat-label">Failed</div>
            </div>
            <div>
              <div className="stat-value">{result.accuracy_percent}%</div>
              <div className="stat-label">Accuracy</div>
            </div>
          </div>
          <p>
            <strong>Average confidence:</strong> {result.average_confidence.toFixed(1)}%
          </p>
          {result.failed_count === 0 ? (
            <span className="badge badge-success">All scenarios passed</span>
          ) : (
            <span className="badge badge-danger">Failures detected</span>
          )}
        </div>
      )}
    </div>
  );
}
