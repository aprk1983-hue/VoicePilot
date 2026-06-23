import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InvestigationTimeline } from "./InvestigationTimeline";
import type { InvestigationStatusData } from "../../api/types";

const STATUS: InvestigationStatusData = {
  case_id: "CASE-1",
  playbook_id: "VP-CUBE-0001",
  state: "ANALYSIS",
  finding_count: 3,
  hypothesis_count: 1,
  recommendation_count: 0,
  top_hypothesis: "Provider SIP service unavailable",
  confidence: 98,
};

describe("InvestigationTimeline", () => {
  it("renders pipeline stages and hypothesis", () => {
    render(<InvestigationTimeline status={STATUS} />);

    expect(screen.getByText("Investigation Timeline")).toBeInTheDocument();
    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(screen.getByText(/Provider SIP service unavailable/)).toBeInTheDocument();
  });
});
