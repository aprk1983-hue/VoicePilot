import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { CaseGrid } from "./CaseGrid";
import type { CaseData } from "../../api/types";

const CASES: CaseData[] = [
  {
    case_id: "CASE-001",
    playbook_id: "VP-CUBE-0001",
    state: "INTAKE",
    finding_count: 0,
    hypothesis_count: 0,
    recommendation_count: 0,
  },
  {
    case_id: "CASE-002",
    playbook_id: "VP-GENESYS-0001",
    state: "ANALYSIS",
    finding_count: 5,
    hypothesis_count: 2,
    recommendation_count: 0,
  },
];

describe("CaseGrid", () => {
  it("renders cases and filters by search", () => {
    render(
      <MemoryRouter>
        <CaseGrid cases={CASES} />
      </MemoryRouter>,
    );

    expect(screen.getByText("CASE-001")).toBeInTheDocument();
    expect(screen.getByText("CASE-002")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search cases"), {
      target: { value: "GENESYS" },
    });

    expect(screen.queryByText("CASE-001")).not.toBeInTheDocument();
    expect(screen.getByText("CASE-002")).toBeInTheDocument();
  });
});
