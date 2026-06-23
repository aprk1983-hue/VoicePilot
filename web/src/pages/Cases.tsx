import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";

export function CasesPage() {
  const { data, loading, error, reload } = useAsync(() => api.listCases(), []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 className="page-title">Cases</h1>
        <Link className="btn" to="/cases/new">
          New Case
        </Link>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingState message="Loading cases…" />
      ) : !data?.length ? (
        <div className="empty-state">
          No cases yet. <Link to="/cases/new">Create your first case</Link>.
        </div>
      ) : (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Playbook</th>
                <th>State</th>
                <th>Findings</th>
                <th>Hypotheses</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.case_id}>
                  <td>
                    <Link to={`/cases/${item.case_id}`}>{item.case_id}</Link>
                  </td>
                  <td>{item.playbook_id}</td>
                  <td>
                    <span className="badge">{item.state}</span>
                  </td>
                  <td>{item.finding_count}</td>
                  <td>{item.hypothesis_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="actions">
            <button type="button" className="btn btn-secondary" onClick={reload}>
              Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
