import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingState } from "../components/LoadingState";
import { useAsync } from "../hooks/useAsync";

export function DashboardPage() {
  const health = useAsync(() => api.getHealth(), []);
  const version = useAsync(() => api.getVersion(), []);
  const cases = useAsync(() => api.listCases(), []);

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <ErrorBanner message={health.error || version.error || cases.error} />

      <div className="grid-2">
        <div className="card">
          <h2>API Health</h2>
          {health.loading ? (
            <LoadingState message="Checking API…" />
          ) : (
            <p>
              Status:{" "}
              <span className="badge badge-success">{health.data?.status ?? "unknown"}</span>
            </p>
          )}
        </div>

        <div className="card">
          <h2>Platform Version</h2>
          {version.loading ? (
            <LoadingState message="Loading version…" />
          ) : (
            <>
              <div className="stat-value">{version.data?.version}</div>
              <div className="stat-label">
                {version.data?.name} · API {version.data?.api_version}
              </div>
            </>
          )}
        </div>

        <div className="card">
          <h2>Cases</h2>
          {cases.loading ? (
            <LoadingState message="Loading cases…" />
          ) : (
            <>
              <div className="stat-value">{cases.data?.length ?? 0}</div>
              <div className="stat-label">In-memory investigations</div>
            </>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Quick Actions</h2>
        <div className="actions">
          <Link className="btn" to="/cases/new">
            Create Case
          </Link>
          <Link className="btn btn-secondary" to="/cases">
            View Cases
          </Link>
          <Link className="btn btn-secondary" to="/validation">
            Run Validation
          </Link>
        </div>
      </div>
    </div>
  );
}
