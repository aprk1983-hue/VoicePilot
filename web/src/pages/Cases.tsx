import { Link } from "react-router-dom";
import { api } from "../api/client";
import { CaseGrid } from "../components/case/CaseGrid";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { LoadingState } from "../components/ui/LoadingState";
import { useAsync } from "../hooks/useAsync";

export function CasesPage() {
  const { data, loading, error, reload } = useAsync(() => api.listCases(), []);

  async function handleDelete(caseId: string) {
    if (!window.confirm(`Delete case ${caseId}?`)) return;
    await api.deleteCase(caseId);
    reload();
  }

  return (
    <div>
      <header className="page-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 className="page-title">Case Management</h1>
            <p className="page-subtitle">Search, sort, and open investigation cases</p>
          </div>
          <Link className="btn" to="/cases/new">
            New Case
          </Link>
        </div>
      </header>

      <ErrorBanner message={error} />

      {loading ? (
        <LoadingState message="Loading cases…" />
      ) : !data?.length ? (
        <div className="empty-state">
          No cases yet. <Link to="/cases/new">Create your first investigation</Link>.
        </div>
      ) : (
        <CaseGrid cases={data} onDelete={handleDelete} />
      )}
    </div>
  );
}
