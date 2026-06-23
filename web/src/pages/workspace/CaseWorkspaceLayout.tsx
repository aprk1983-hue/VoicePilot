import { Outlet, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { CaseWorkspaceNav } from "../../components/case/CaseWorkspaceNav";
import { Badge } from "../../components/ui/Badge";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingState } from "../../components/ui/LoadingState";
import { useAsync } from "../../hooks/useAsync";

export function CaseWorkspaceLayout() {
  const { caseId = "" } = useParams();
  const { data, loading, error } = useAsync(() => api.getCase(caseId), [caseId]);

  if (loading) return <LoadingState message="Loading workspace…" />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div>
      <header className="workspace-header">
        <h1 className="page-title">{data.case_id}</h1>
        <div className="workspace-meta">
          <Badge variant="accent">{data.state}</Badge>
          <Badge>{data.playbook_id}</Badge>
          <span className="metric-hint">
            {data.finding_count} findings · {data.hypothesis_count} hypotheses
          </span>
        </div>
      </header>
      <CaseWorkspaceNav caseId={caseId} />
      <Outlet context={data} />
    </div>
  );
}
