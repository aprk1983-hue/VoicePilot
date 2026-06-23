import { Navigate, useParams } from "react-router-dom";
import { reportEndpoint } from "../../api/client";
import type { ReportType } from "../../api/types";
import { ReportTabs } from "../../components/reports/ReportTabs";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingState } from "../../components/ui/LoadingState";
import { MarkdownViewer } from "../../components/ui/MarkdownViewer";
import { useAsync } from "../../hooks/useAsync";

export function ReportsRedirect() {
  const { caseId = "" } = useParams();
  return <Navigate to={`/cases/${caseId}/reports/executive`} replace />;
}

export function ReportsTab() {
  const { caseId = "", reportType = "executive" } = useParams();
  const activeType = (reportType as ReportType) || "executive";
  const { data, loading, error } = useAsync(
    () => reportEndpoint(caseId, activeType),
    [caseId, activeType],
  );

  return (
    <div>
      <ReportTabs caseId={caseId} activeType={activeType} />
      <ErrorBanner message={error} />
      {loading ? (
        <LoadingState message="Loading report…" />
      ) : data ? (
        <Card title={`${data.report_type} Report`}>
          <MarkdownViewer content={data.markdown} />
        </Card>
      ) : null}
    </div>
  );
}
