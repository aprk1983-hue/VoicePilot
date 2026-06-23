export interface ApiEnvelope<T> {
  success: boolean;
  request_id: string;
  timestamp: string;
  data: T;
}

export interface ApiErrorBody {
  success: false;
  error: string;
  message: string;
  request_id: string;
  timestamp: string;
  details?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error;
    this.requestId = body.request_id;
  }
}

export interface HealthData {
  status: string;
  service: string;
}

export interface VersionData {
  name: string;
  version: string;
  api_version: string;
}

export interface CaseData {
  case_id: string;
  playbook_id: string;
  state: string;
  finding_count: number;
  hypothesis_count: number;
  recommendation_count: number;
}

export interface EvidenceData {
  case_id: string;
  evidence_id: string;
  command: string;
  accepted: boolean;
}

export interface InvestigationStatusData extends CaseData {
  top_hypothesis: string | null;
  confidence: number | null;
}

export interface AnalysisData {
  case_id: string;
  finding_count: number;
  top_hypothesis: string | null;
  confidence: number | null;
}

export interface DiscoveryData {
  case_id: string;
  current_confidence: number;
  estimated_final_confidence: number;
  next_best_command: string | null;
  request_count: number;
}

export interface QualityData {
  case_id: string;
  overall_score: number;
  overall_status: string;
  ready_for_recommendation: boolean;
  ready_for_case_closure: boolean;
}

export interface RecommendationData {
  case_id: string;
  recommendation_count: number;
  top_recommendation: string | null;
}

export interface ChangePackageData {
  case_id: string;
  package_id: string;
  risk_level: string;
  title: string;
  markdown: string;
}

export interface ReportData {
  case_id: string;
  report_id?: string;
  report_type: string;
  markdown: string;
}

export interface InvestigationData {
  case_id: string;
  analysis: AnalysisData;
  discovery: DiscoveryData;
  quality: QualityData;
  recommendation: RecommendationData;
  change_package: ChangePackageData;
}

export interface ValidationData {
  playbook_id: string | null;
  total_scenarios: number;
  passed_count: number;
  failed_count: number;
  accuracy_percent: number;
  average_confidence: number;
}

export type ReportType = "executive" | "engineering" | "cab";

export const SUPPORTED_PLAYBOOKS = [
  "VP-CUBE-0001",
  "VP-CUCM-0001",
  "VP-TEAMS-0001",
  "VP-AUDIOCODES-0001",
  "VP-GENESYS-0001",
] as const;
