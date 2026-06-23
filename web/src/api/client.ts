import type {
  ApiEnvelope,
  ApiErrorBody,
  CaseData,
  ChangePackageData,
  EvidenceData,
  HealthData,
  InvestigationData,
  InvestigationStatusData,
  ReportData,
  ReportType,
  ValidationData,
  VersionData,
} from "./types";
import { ApiError } from "./types";

const DEFAULT_BASE = "http://localhost:8000";

export function getApiBase(): string {
  return import.meta.env.VITE_API_BASE ?? DEFAULT_BASE;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  const body = (await response.json()) as ApiEnvelope<T> | ApiErrorBody;

  if (!response.ok || !("success" in body) || body.success === false) {
    throw new ApiError(response.status, body as ApiErrorBody);
  }

  return (body as ApiEnvelope<T>).data;
}

export const api = {
  getHealth: () => request<HealthData>("/health"),
  getVersion: () => request<VersionData>("/version"),

  createCase: (playbookId: string) =>
    request<CaseData>("/cases", {
      method: "POST",
      body: JSON.stringify({ playbook_id: playbookId }),
    }),

  listCases: () => request<CaseData[]>("/cases"),
  getCase: (caseId: string) => request<CaseData>(`/cases/${caseId}`),
  deleteCase: (caseId: string) =>
    request<{ case_id: string; deleted: boolean }>(`/cases/${caseId}`, {
      method: "DELETE",
    }),

  uploadEvidence: (caseId: string, command: string, content: string) =>
    request<EvidenceData>(`/cases/${caseId}/evidence`, {
      method: "POST",
      body: JSON.stringify({ command, content }),
    }),

  investigateCase: (caseId: string) =>
    request<InvestigationData>(`/cases/${caseId}/investigate`, {
      method: "POST",
    }),

  getInvestigationStatus: (caseId: string) =>
    request<InvestigationStatusData>(`/cases/${caseId}/status`),

  getExecutiveReport: (caseId: string) =>
    request<ReportData>(`/cases/${caseId}/executive`),
  getEngineeringReport: (caseId: string) =>
    request<ReportData>(`/cases/${caseId}/engineering`),
  getCabReport: (caseId: string) =>
    request<ReportData>(`/cases/${caseId}/cab`),

  getChangePackage: (caseId: string) =>
    request<ChangePackageData>(`/cases/${caseId}/change-package`),

  validate: (playbookId?: string | null) =>
    request<ValidationData>("/validate", {
      method: "POST",
      body: JSON.stringify({ playbook_id: playbookId ?? null }),
    }),
};

export function reportEndpoint(caseId: string, type: ReportType): Promise<ReportData> {
  switch (type) {
    case "executive":
      return api.getExecutiveReport(caseId);
    case "engineering":
      return api.getEngineeringReport(caseId);
    case "cab":
      return api.getCabReport(caseId);
  }
}
