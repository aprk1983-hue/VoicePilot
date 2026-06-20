"""Deterministic investigation quality evaluation engine."""

from __future__ import annotations

from datetime import datetime, timezone

from domain.models import Case
from investigation_quality.quality_bootstrap import default_quality_registry
from investigation_quality.quality_models import (
    InvestigationQualityReport,
    QualityMetricResult,
    QualityStatus,
)
from investigation_quality.quality_registry import InvestigationQualityRegistry

_READY_FOR_RECOMMENDATION_MIN_SCORE = 75


class InvestigationQualityEngine:
    """Evaluate investigation quality using registered metrics."""

    def __init__(self, registry: InvestigationQualityRegistry | None = None) -> None:
        self._registry = registry or default_quality_registry()

    @property
    def registry(self) -> InvestigationQualityRegistry:
        """Return the quality metric registry."""
        return self._registry

    def evaluate_case(self, case: Case) -> InvestigationQualityReport:
        """Evaluate all registered metrics and build a quality report."""
        metric_results = self._registry.evaluate(case)
        overall_score = _calculate_overall_score(metric_results)
        overall_status = _overall_status(overall_score)
        return InvestigationQualityReport(
            overall_score=overall_score,
            overall_status=overall_status,
            metric_results=metric_results,
            ready_for_recommendation=overall_score >= _READY_FOR_RECOMMENDATION_MIN_SCORE,
            ready_for_case_closure=overall_score == 100,
            generated_at=datetime.now(timezone.utc),
        )


def _calculate_overall_score(metric_results: tuple[QualityMetricResult, ...]) -> int:
    if not metric_results:
        return 0
    total = sum(result.score for result in metric_results)
    return round(total / len(metric_results))


def _overall_status(overall_score: int) -> str:
    if overall_score >= 90:
        return QualityStatus.PASS
    if overall_score >= 50:
        return QualityStatus.WARN
    return QualityStatus.FAIL
