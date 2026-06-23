"""Pydantic response models for the VoicePilot REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApiEnvelope(BaseModel):
    """Standard success envelope for API responses."""

    success: bool = True
    request_id: str
    timestamp: datetime
    data: dict | list | str | int | float | bool | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope for API responses."""

    success: bool = False
    error: str
    message: str
    request_id: str
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = "ok"
    service: str = "voicepilot-api"


class VersionResponse(BaseModel):
    """Version metadata payload."""

    name: str
    version: str
    api_version: str = "v1"


class CaseResponse(BaseModel):
    """Investigation case summary."""

    case_id: str
    playbook_id: str
    state: str
    finding_count: int
    hypothesis_count: int
    recommendation_count: int


class EvidenceResponse(BaseModel):
    """Evidence upload result."""

    case_id: str
    evidence_id: str
    command: str
    accepted: bool


class AnalysisResponse(BaseModel):
    """Analysis pipeline result."""

    case_id: str
    finding_count: int
    top_hypothesis: str | None
    confidence: float | None


class DiscoveryResponse(BaseModel):
    """Discovery plan result."""

    case_id: str
    current_confidence: float
    estimated_final_confidence: float
    next_best_command: str | None
    request_count: int


class QualityResponse(BaseModel):
    """Investigation quality evaluation result."""

    case_id: str
    overall_score: int
    overall_status: str
    ready_for_recommendation: bool
    ready_for_case_closure: bool


class RecommendationResponse(BaseModel):
    """Recommendation generation result."""

    case_id: str
    recommendation_count: int
    top_recommendation: str | None


class ChangePackageResponse(BaseModel):
    """Engineering change package result."""

    case_id: str
    package_id: str
    risk_level: str
    title: str
    markdown: str


class ReportResponse(BaseModel):
    """Enterprise report result."""

    case_id: str
    report_id: str
    report_type: str
    markdown: str


class InvestigationStatusResponse(BaseModel):
    """Current investigation status."""

    case_id: str
    playbook_id: str
    state: str
    finding_count: int
    hypothesis_count: int
    recommendation_count: int
    top_hypothesis: str | None
    confidence: float | None


class InvestigationResponse(BaseModel):
    """Full investigation pipeline result."""

    case_id: str
    analysis: AnalysisResponse
    discovery: DiscoveryResponse
    quality: QualityResponse
    recommendation: RecommendationResponse
    change_package: ChangePackageResponse


class BrainSessionResponse(BaseModel):
    """Brain orchestration session summary."""

    session_id: str
    case_id: str
    playbook_id: str
    current_stage: str
    current_confidence: float | None
    current_quality_score: int | None
    completed: bool
    failed: bool


class BrainTimelineResponse(BaseModel):
    """Brain session replay timeline."""

    session_id: str
    markdown: str


class ValidationResponse(BaseModel):
    """Validation suite summary."""

    playbook_id: str | None
    total_scenarios: int
    passed_count: int
    failed_count: int
    accuracy_percent: float
    average_confidence: float


class DeleteCaseResponse(BaseModel):
    """Case deletion confirmation."""

    case_id: str
    deleted: bool = True


class MarkdownReportResponse(BaseModel):
    """Markdown-only report wrapper."""

    case_id: str
    report_type: str
    markdown: str = Field(..., description="Report body in Markdown")
