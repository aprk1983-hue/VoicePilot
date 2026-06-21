"""Immutable models for the Investigation Comparison Engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


READ_ONLY_NOTICE = (
    "VoicePilot is read-only. Comparison reports summarize existing investigation outputs only. "
    "VoicePilot does not diagnose, recommend, or execute configuration changes."
)


class ComparisonStatus(str, Enum):
    """Overall before/after comparison status."""

    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    REGRESSED = "REGRESSED"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class ImprovementMetric:
    """Single metric delta between before and after investigations."""

    name: str
    before_value: str
    after_value: str
    delta: str
    improved: bool


@dataclass(frozen=True)
class FindingComparison:
    """Comparison of one finding signal between investigations."""

    finding: str
    before: bool
    after: bool
    resolved: bool


@dataclass(frozen=True)
class InvestigationSnapshot:
    """Read-only metrics extracted from a case or configuration snapshot."""

    source_id: str
    health_score: int | None
    confidence: float | None
    quality_score: int | None
    knowledge_matches: tuple[str, ...]
    critical_findings: tuple[str, ...]
    finding_signals: tuple[str, ...]
    verification_status: str | None


@dataclass(frozen=True)
class InvestigationComparison:
    """Deterministic before/after investigation comparison."""

    comparison_id: str
    generated_at: datetime
    before_case_id: str
    after_case_id: str
    status: ComparisonStatus
    summary: str
    health_score_before: int | None
    health_score_after: int | None
    confidence_before: float | None
    confidence_after: float | None
    quality_before: int | None
    quality_after: int | None
    knowledge_matches_before: tuple[str, ...]
    knowledge_matches_after: tuple[str, ...]
    critical_findings_before: tuple[str, ...]
    critical_findings_after: tuple[str, ...]
    resolved_findings: tuple[str, ...]
    remaining_findings: tuple[str, ...]
    new_findings: tuple[str, ...]
    verification_status: str
    improvement_metrics: tuple[ImprovementMetric, ...]
    finding_comparisons: tuple[FindingComparison, ...]
    read_only_notice: str = READ_ONLY_NOTICE
