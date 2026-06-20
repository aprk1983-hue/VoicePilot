"""Investigation quality domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class QualityStatus:
    """Deterministic quality status labels."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QualityMetricResult:
    """Result of evaluating one investigation quality metric."""

    metric_name: str
    score: int
    max_score: int
    status: str
    summary: str
    recommendations: tuple[str, ...]


@dataclass(frozen=True)
class InvestigationQualityReport:
    """Aggregated investigation quality evaluation for a case."""

    overall_score: int
    overall_status: str
    metric_results: tuple[QualityMetricResult, ...]
    ready_for_recommendation: bool
    ready_for_case_closure: bool
    generated_at: datetime
