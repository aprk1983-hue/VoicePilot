import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingState } from "../../components/ui/LoadingState";
import { MarkdownViewer } from "../../components/ui/MarkdownViewer";
import { useAsync } from "../../hooks/useAsync";

export function ChangePackageTab() {
  const { caseId = "" } = useParams();
  const { data, loading, error } = useAsync(() => api.getChangePackage(caseId), [caseId]);

  if (loading) return <LoadingState message="Loading change package…" />;

  return (
    <div>
      <ErrorBanner message={error} />
      {data && (
        <Card title={data.title}>
          <p>
            <strong>Package:</strong> {data.package_id}
          </p>
          <p>
            <strong>Risk level:</strong> {data.risk_level}
          </p>
          <p className="metric-hint">
            Advisory only — VoicePilot never performs configuration changes.
          </p>
          <MarkdownViewer content={data.markdown} />
        </Card>
      )}
    </div>
  );
}
