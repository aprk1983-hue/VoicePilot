import { Link } from "react-router-dom";
import { api } from "../api/client";
import { MetricCard } from "../components/ui/MetricCard";
import { Card } from "../components/ui/Card";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { LoadingState } from "../components/ui/LoadingState";
import { Badge } from "../components/ui/Badge";
import { useAsync } from "../hooks/useAsync";

export function DashboardPage() {
  const { data, loading, error } = useAsync(() => api.getDashboardSummary(), []);

  if (loading) return <LoadingState message="Loading dashboard…" />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Platform health and investigation metrics — advisory read-only mode
        </p>
      </header>

      <div className="metrics-grid">
        <MetricCard label="Active Cases" value={data.total_cases} hint="In-memory investigations" />
        <MetricCard label="Total Findings" value={data.total_findings} />
        <MetricCard label="Hypotheses" value={data.total_hypotheses} />
        <MetricCard label="Recommendations" value={data.total_recommendations} />
        <MetricCard label="Knowledge Assets" value={data.knowledge_asset_count} />
        <MetricCard
          label="Supported Playbooks"
          value={data.supported_playbook_count}
        />
      </div>

      <div className="health-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="health-card status-ok">
          <div className="health-status">
            <span className="health-dot" />
            API {data.api_status.toUpperCase()}
          </div>
          <p style={{ margin: "0.75rem 0 0", color: "var(--vp-muted)", fontSize: "0.9rem" }}>
            {data.platform_name} v{data.platform_version} · API {data.api_version}
          </p>
        </div>
        <Card className="card-flat">
          <h2 className="card-title">Read-Only Notice</h2>
          <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--vp-text-secondary)" }}>
            {data.read_only_notice}
          </p>
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Cases by State">
          {Object.keys(data.cases_by_state).length === 0 ? (
            <p className="metric-hint">No cases yet.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {Object.entries(data.cases_by_state).map(([state, count]) => (
                <li key={state}>
                  <Badge variant="accent">{state}</Badge> — {count}
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Cases by Playbook">
          {Object.keys(data.cases_by_playbook).length === 0 ? (
            <p className="metric-hint">No playbook activity yet.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
              {Object.entries(data.cases_by_playbook).map(([playbook, count]) => (
                <li key={playbook}>
                  {playbook} — {count}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Quick Actions">
        <div className="actions">
          <Link className="btn" to="/cases/new">
            Create Case
          </Link>
          <Link className="btn btn-secondary" to="/cases">
            Case Management
          </Link>
          <Link className="btn btn-secondary" to="/validation">
            Run Validation
          </Link>
        </div>
      </Card>
    </div>
  );
}
