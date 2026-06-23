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
class ComparisonResult:
    """Generated investigation comparison result."""

    comparison_id: str
    status: str
    summary: str
    markdown: str
    before_case_id: str
    after_case_id: str


@dataclass(frozen=True)
class ReportResult:
    """Generated enterprise report for any audience."""

    case_id: str
    report_id: str
    report_type: str
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
class AssetValidationResult:
    """Result of validating engineering assets."""

    valid: bool
    total_assets: int
    invalid_count: int
    duplicate_ids: tuple[str, ...]
    duplicate_titles: tuple[str, ...]


@dataclass(frozen=True)
class AssetStatisticsResult:
    """Aggregate statistics for engineering assets."""

    total_assets: int
    average_quality: float
    missing_references: int
    relationship_count: int
    duplicate_ids: tuple[str, ...]
    vendor_counts: tuple[tuple[str, int], ...]
    product_counts: tuple[tuple[str, int], ...]
    category_counts: tuple[tuple[str, int], ...]


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


@dataclass(frozen=True)
class ServiceInvestigationStatusResult:
    """Current investigation pipeline status for a case."""

    case_id: str
    playbook_id: str
    state: str
    finding_count: int
    hypothesis_count: int
    recommendation_count: int
    top_hypothesis: str | None
    confidence: float | None


@dataclass(frozen=True)
class ServiceInvestigationResult:
    """Result of running the full investigation pipeline for a case."""

    case_id: str
    analysis: ServiceAnalysisResult
    discovery: ServiceDiscoveryResult
    quality: ServiceQualityResult
    recommendation: ServiceRecommendationResult
    change_package: ServiceChangePackageResult


@dataclass(frozen=True)
class ServiceValidationResult:
    """Result of validating one or more playbook scenario packs."""

    playbook_id: str | None
    total_scenarios: int
    passed_count: int
    failed_count: int
    accuracy_percent: float
    average_confidence: float
