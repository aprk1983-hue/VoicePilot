import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { SUPPORTED_PLAYBOOKS } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";

export function NewCasePage() {
  const navigate = useNavigate();
  const [playbookId, setPlaybookId] = useState<string>(SUPPORTED_PLAYBOOKS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const created = await api.createCase(playbookId);
      navigate(`/cases/${created.case_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">New Case</h1>
      <ErrorBanner message={error} />

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="playbook">Playbook</label>
          <select
            id="playbook"
            value={playbookId}
            onChange={(event) => setPlaybookId(event.target.value)}
          >
            {SUPPORTED_PLAYBOOKS.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>

        <div className="actions">
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create Case"}
          </button>
          <Link className="btn btn-secondary" to="/cases">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
