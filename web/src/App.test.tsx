import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ThemeProvider } from "./context/ThemeProvider";
import { App } from "./App";

vi.mock("./api/client", () => ({
  api: {
    getDashboardSummary: vi.fn().mockResolvedValue({
      api_status: "ok",
      platform_name: "voicepilot",
      platform_version: "0.1.0",
      api_version: "v1",
      total_cases: 2,
      cases_by_state: { INTAKE: 2 },
      cases_by_playbook: { "VP-CUBE-0001": 2 },
      total_findings: 0,
      total_hypotheses: 0,
      total_recommendations: 0,
      knowledge_asset_count: 100,
      supported_playbook_count: 5,
      supported_playbooks: ["VP-CUBE-0001"],
      read_only_notice: "Advisory only.",
    }),
    listCases: vi.fn().mockResolvedValue([]),
  },
  getApiBase: () => "http://localhost:8000",
  reportEndpoint: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("voicepilot-theme", "dark");
  });

  it("renders enterprise dashboard with metrics", async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByText("Active Cases")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText(/Evidence-only · Deterministic/i)).toBeInTheDocument();
  });

  it("renders sidebar navigation", () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/cases"]}>
          <App />
        </MemoryRouter>
      </ThemeProvider>,
    );

    const nav = screen.getByRole("navigation");
    expect(within(nav).getByRole("link", { name: "Cases" })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "Validation" })).toBeInTheDocument();
  });
});
