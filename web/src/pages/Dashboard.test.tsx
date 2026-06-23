import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeProvider } from "../context/ThemeProvider";
import { DashboardPage } from "./Dashboard";

vi.mock("../api/client", () => ({
  api: {
    getDashboardSummary: vi.fn(),
  },
}));

import { api } from "../api/client";

const mockSummary = {
  api_status: "ok",
  platform_name: "voicepilot",
  platform_version: "0.1.0",
  api_version: "v1",
  total_cases: 5,
  cases_by_state: { INTAKE: 3, INVESTIGATING: 2 },
  cases_by_playbook: { "VP-CUBE-0001": 5 },
  total_findings: 10,
  total_hypotheses: 4,
  total_recommendations: 2,
  knowledge_asset_count: 200,
  supported_playbook_count: 5,
  supported_playbooks: ["VP-CUBE-0001"],
  read_only_notice: "Advisory only.",
};

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(api.getDashboardSummary).mockResolvedValue(mockSummary);
  });

  it("loads and displays dashboard metrics", async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Active Cases").closest(".metric-card")).toHaveTextContent("5");
    expect(screen.getByText("Advisory only.")).toBeInTheDocument();
    expect(api.getDashboardSummary).toHaveBeenCalled();
  });
});
