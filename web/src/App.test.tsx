import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { App } from "./App";

vi.mock("./api/client", () => ({
  api: {
    getHealth: vi.fn().mockResolvedValue({ status: "ok", service: "voicepilot-api" }),
    getVersion: vi.fn().mockResolvedValue({
      name: "voicepilot",
      version: "0.1.0",
      api_version: "v1",
    }),
    listCases: vi.fn().mockResolvedValue([]),
  },
  getApiBase: () => "http://localhost:8000",
  reportEndpoint: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dashboard with read-only notice", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("VoicePilot Enterprise")).toBeInTheDocument();
    expect(
      screen.getByText(/VoicePilot never performs configuration changes/i),
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(
      <MemoryRouter initialEntries={["/cases"]}>
        <App />
      </MemoryRouter>,
    );

    const nav = screen.getByRole("navigation");
    expect(within(nav).getByRole("link", { name: "Cases" })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "New Case" })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "Validation" })).toBeInTheDocument();
  });
});
