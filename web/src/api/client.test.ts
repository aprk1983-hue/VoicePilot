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
});
