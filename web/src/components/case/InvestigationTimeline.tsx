import type { InvestigationStatusData } from "../../api/types";
import { Badge } from "../ui/Badge";

const PIPELINE_STAGES: { key: string; label: string; states: string[] }[] = [
  { key: "INTAKE", label: "Intake", states: ["NEW", "INTAKE"] },
  { key: "COLLECTION", label: "Evidence Collection", states: ["DISCOVERY", "COLLECTION"] },
  { key: "ANALYSIS", label: "Analysis", states: ["ANALYSIS"] },
  { key: "HYPOTHESIS", label: "Hypothesis Generation", states: ["HYPOTHESIS"] },
  { key: "INVESTIGATION", label: "Correlation & Investigation", states: ["INVESTIGATION"] },
  { key: "RESOLUTION", label: "Recommendation", states: ["RESOLUTION"] },
  { key: "CLOSED", label: "Verification & Closure", states: ["VERIFICATION", "CLOSED"] },
];

function stageStatus(
  _stageStates: string[],
  currentState: string,
  stageIndex: number,
): "complete" | "active" | "pending" {
  const currentIndex = PIPELINE_STAGES.findIndex((stage) =>
    stage.states.includes(currentState),
  );
  if (currentIndex > stageIndex) return "complete";
  if (currentIndex === stageIndex) return "active";
  return "pending";
}

interface InvestigationTimelineProps {
  status: InvestigationStatusData;
}

export function InvestigationTimeline({ status }: InvestigationTimelineProps) {
  return (
    <div className="card card-flat">
      <div className="card-header">
        <h2 className="card-title">Investigation Timeline</h2>
        <Badge variant="accent">{status.state}</Badge>
      </div>
      <div className="timeline">
        {PIPELINE_STAGES.map((stage, index) => {
          const itemStatus = stageStatus(stage.states, status.state, index);
          return (
            <div key={stage.key} className={`timeline-item ${itemStatus}`}>
              <div className="timeline-dot" />
              <div className="timeline-title">{stage.label}</div>
              <div className="timeline-meta">
                {itemStatus === "complete" && "Completed"}
                {itemStatus === "active" && "In progress"}
                {itemStatus === "pending" && "Pending"}
              </div>
            </div>
          );
        })}
      </div>
      {status.top_hypothesis && (
        <p style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
          <strong>Top hypothesis:</strong> {status.top_hypothesis}
          {status.confidence != null && ` (${status.confidence}% confidence)`}
        </p>
      )}
    </div>
  );
}
