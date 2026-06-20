"""Built-in investigation quality metrics."""

from __future__ import annotations

from dataclasses import dataclass

from discovery.planner_engine import PlannerEngine
from discovery.planner_models import DiscoveryPlan, DiscoveryPriority, DiscoveryRequest
from domain.models import Case
from investigation_quality.quality_metric import InvestigationQualityMetric
from investigation_quality.quality_models import QualityMetricResult, QualityStatus

EVIDENCE_COMPLETENESS_METRIC_NAME = "evidence_completeness"
MAX_SCORE = 100
_CRITICAL_PRIORITIES = frozenset({DiscoveryPriority.CRITICAL, DiscoveryPriority.HIGH})
_READY_FOR_RECOMMENDATION_MIN_SCORE = 75


def _resolve_discovery_plan(case: Case) -> DiscoveryPlan:
    if case.discovery_plan is not None:
        return case.discovery_plan
    return PlannerEngine().evaluate_case(case)


def _missing_requests(plan: DiscoveryPlan) -> tuple[DiscoveryRequest, ...]:
    return plan.requests


def _missing_critical_requests(plan: DiscoveryPlan) -> tuple[DiscoveryRequest, ...]:
    return tuple(
        request
        for request in plan.requests
        if request.priority in _CRITICAL_PRIORITIES and not request.optional
    )


def _missing_optional_requests(plan: DiscoveryPlan) -> tuple[DiscoveryRequest, ...]:
    return tuple(request for request in plan.requests if request.optional)


def _score_evidence_completeness(case: Case, plan: DiscoveryPlan) -> int:
    if not case.evidence:
        return 0

    missing_critical = _missing_critical_requests(plan)
    if not plan.requests:
        return MAX_SCORE
    if len(missing_critical) == 1:
        return 75
    if len(missing_critical) >= 2:
        return 50
    return MAX_SCORE


def _status_for_score(score: int) -> str:
    if score >= 90:
        return QualityStatus.PASS
    if score >= 50:
        return QualityStatus.WARN
    return QualityStatus.FAIL


def _build_recommendations(plan: DiscoveryPlan) -> tuple[str, ...]:
    recommendations: list[str] = []
    for request in sorted(plan.requests, key=lambda item: (-item.score, item.command)):
        recommendations.append(
            f"Collect missing evidence: `{request.command}` "
            f"({request.priority.value}) — {request.reason}"
        )
    return tuple(recommendations)


def _build_summary(case: Case, plan: DiscoveryPlan, score: int) -> str:
    if not case.evidence:
        return "No investigative evidence has been collected."

    if not plan.requests:
        return "All required and optional discovery evidence has been collected."

    missing_critical = _missing_critical_requests(plan)
    missing_optional = _missing_optional_requests(plan)
    if len(missing_critical) == 1:
        request = missing_critical[0]
        return (
            f"One critical evidence item is missing: `{request.command}` "
            f"({request.priority.value})."
        )
    if len(missing_critical) >= 2:
        commands = ", ".join(f"`{request.command}`" for request in missing_critical)
        return f"Multiple critical evidence items are missing: {commands}."

    if missing_optional:
        commands = ", ".join(f"`{request.command}`" for request in missing_optional)
        return f"Required evidence is complete; optional evidence still missing: {commands}."

    remaining = ", ".join(f"`{request.command}`" for request in plan.requests)
    return f"Evidence gaps remain: {remaining}."


@dataclass(frozen=True)
class EvidenceCompletenessMetric(InvestigationQualityMetric):
    """Score evidence completeness using the discovery plan."""

    name: str = EVIDENCE_COMPLETENESS_METRIC_NAME
    title: str = "Evidence Completeness"

    def evaluate(self, case: Case) -> QualityMetricResult:
        plan = _resolve_discovery_plan(case)
        score = _score_evidence_completeness(case, plan)
        return QualityMetricResult(
            metric_name=self.name,
            score=score,
            max_score=MAX_SCORE,
            status=_status_for_score(score),
            summary=_build_summary(case, plan, score),
            recommendations=_build_recommendations(plan),
        )


BUILTIN_QUALITY_METRICS: tuple[InvestigationQualityMetric, ...] = (
    EvidenceCompletenessMetric(),
)


def register_builtin_metrics(registry) -> None:
    """Register built-in investigation quality metrics."""
    for metric in BUILTIN_QUALITY_METRICS:
        registry.register_metric(metric)
