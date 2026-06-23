import { Link, useOutletContext } from "react-router-dom";
import type { CaseData } from "../../api/types";
import { Card } from "../../components/ui/Card";

export function OverviewTab() {
  const caseData = useOutletContext<CaseData>();

  return (
    <div className="grid-2">
      <Card title="Investigation Summary">
        <p>
          <strong>Playbook:</strong> {caseData.playbook_id}
        </p>
        <p>
          <strong>State:</strong> {caseData.state}
        </p>
        <p>
          <strong>Findings:</strong> {caseData.finding_count}
        </p>
        <p>
          <strong>Hypotheses:</strong> {caseData.hypothesis_count}
        </p>
        <p>
          <strong>Recommendations:</strong> {caseData.recommendation_count}
        </p>
      </Card>
      <Card title="Workspace Actions">
        <div className="actions">
          <Link className="btn btn-secondary" to={`/cases/${caseData.case_id}/evidence`}>
            Upload Evidence
          </Link>
          <Link className="btn btn-secondary" to={`/cases/${caseData.case_id}/investigation`}>
            Run Investigation
          </Link>
          <Link className="btn btn-secondary" to={`/cases/${caseData.case_id}/reports/executive`}>
            View Reports
          </Link>
          <Link className="btn btn-secondary" to={`/cases/${caseData.case_id}/change-package`}>
            Change Package
          </Link>
        </div>
      </Card>
    </div>
  );
}
