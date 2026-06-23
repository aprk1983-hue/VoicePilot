import { describe, expect, it, vi, beforeEach } from "vitest";
import { ApiError } from "../api/types";
import { api, getApiBase } from "../api/client";

describe("getApiBase", () => {
  it("defaults to localhost backend", () => {
    expect(getApiBase()).toBe("http://localhost:8000");
  });
});

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("unwraps success envelopes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          request_id: "req-1",
          timestamp: "2026-06-19T00:00:00Z",
          data: { status: "ok", service: "voicepilot-api" },
        }),
      }),
    );

    const health = await api.getHealth();
    expect(health.status).toBe("ok");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("throws ApiError on failure responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({
          success: false,
          error: "case_not_found",
          message: "Case not found: CASE-missing",
          request_id: "req-2",
          timestamp: "2026-06-19T00:00:00Z",
        }),
      }),
    );

    await expect(api.getCase("CASE-missing")).rejects.toBeInstanceOf(ApiError);
  });

  it("creates cases with playbook id", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          request_id: "req-3",
          timestamp: "2026-06-19T00:00:00Z",
          data: {
            case_id: "CASE-1",
            playbook_id: "VP-CUBE-0001",
            state: "INTAKE",
            finding_count: 0,
            hypothesis_count: 0,
            recommendation_count: 0,
          },
        }),
      }),
    );

    const created = await api.createCase("VP-CUBE-0001");
    expect(created.case_id).toBe("CASE-1");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/cases",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ playbook_id: "VP-CUBE-0001" }),
      }),
    );
  });

  it("loads dashboard summary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          request_id: "req-4",
          timestamp: "2026-06-19T00:00:00Z",
          data: {
            api_status: "ok",
            platform_name: "voicepilot",
            platform_version: "0.1.0",
            api_version: "v1",
            total_cases: 1,
            cases_by_state: { INTAKE: 1 },
            cases_by_playbook: { "VP-CUBE-0001": 1 },
            total_findings: 0,
            total_hypotheses: 0,
            total_recommendations: 0,
            knowledge_asset_count: 50,
            supported_playbook_count: 5,
            supported_playbooks: ["VP-CUBE-0001"],
            read_only_notice: "Advisory only.",
          },
        }),
      }),
    );

    const summary = await api.getDashboardSummary();
    expect(summary.total_cases).toBe(1);
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/dashboard/summary",
      expect.any(Object),
    );
  });
});
