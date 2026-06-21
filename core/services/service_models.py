"""Public DTO models for the VoicePilot service layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCaseResult:
    """Summary view of an investigation case."""

    case_id: str
    playbook_id: str
    state: str
    finding_count: int
    hypothesis_count: int
    recommendation_count: int


@dataclass(frozen=True)
class ServiceEvidenceResult:
    """Result of uploading CLI evidence to a case."""

    case_id: str
    evidence_id: str
    command: str
    accepted: bool


@dataclass(frozen=True)
class ServiceAnalysisResult:
    """Result of analyzing collected evidence for a case."""

    case_id: str
    finding_count: int
    top_hypothesis: str | None
    confidence: float | None


@dataclass(frozen=True)
class ServiceDiscoveryResult:
    """Result of generating a discovery plan for a case."""

    case_id: str
    current_confidence: float
    estimated_final_confidence: float
    next_best_command: str | None
    request_count: int


@dataclass(frozen=True)
class ServiceQualityResult:
    """Result of evaluating investigation quality for a case."""

    case_id: str
    overall_score: int
    overall_status: str
    ready_for_recommendation: bool
    ready_for_case_closure: bool


@dataclass(frozen=True)
class ServiceRecommendationResult:
    """Result of generating a recommendation for a case."""

    case_id: str
    recommendation_count: int
    top_recommendation: str | None


@dataclass(frozen=True)
class ServiceReportResult:
    """Generated incident report for a closed case."""

    case_id: str
    markdown: str


@dataclass(frozen=True)
class ServiceChangePackageResult:
    """Generated read-only engineering change package."""

    case_id: str
    package_id: str
    risk_level: str
    title: str
    markdown: str


@dataclass(frozen=True)
class ServiceBrainSessionResult:
    """Summary view of a Brain orchestration session."""

    session_id: str
    case_id: str
    playbook_id: str
    current_stage: str
    current_confidence: float | None
    current_quality_score: int | None
    completed: bool
    failed: bool
