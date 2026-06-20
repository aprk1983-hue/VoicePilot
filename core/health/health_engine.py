"""Deterministic health evaluation engine."""

from __future__ import annotations

from domain.models import Case
from health.builtin_rules import register_builtin_rules
from health.health_models import HealthResult, HealthStatus
from health.health_report import HealthReport
from health.health_rule_registry import HealthRuleRegistry
from health.health_severity import HealthSeverity
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology
from topology.topology_builder import TopologyBuilder

_BASE_SCORE = 100
_SEVERITY_PENALTIES: dict[HealthSeverity, int] = {
    HealthSeverity.CRITICAL: 30,
    HealthSeverity.HIGH: 15,
    HealthSeverity.MEDIUM: 10,
    HealthSeverity.LOW: 5,
    HealthSeverity.INFO: 0,
}
_ACTIVE_STATUSES = frozenset({HealthStatus.WARN, HealthStatus.FAIL})


class HealthEngine:
    """Evaluate canonical voice objects and topology using registered health rules."""

    def __init__(self, registry: HealthRuleRegistry | None = None) -> None:
        self._registry = registry or default_health_rule_registry()

    def evaluate_object(self, obj: VoiceObject, topology: VoiceTopology) -> tuple[HealthResult, ...]:
        """Evaluate all applicable rules for one object."""
        results = [
            rule.evaluate(obj, topology)
            for rule in self._registry.rules_for_object_type(obj.object_type)
        ]
        return tuple(sorted(results, key=_result_sort_key))

    def evaluate_topology(self, topology: VoiceTopology) -> HealthReport:
        """Evaluate all objects in a topology."""
        results: list[HealthResult] = []
        for obj in sorted(topology.all_objects(), key=lambda item: item.id):
            results.extend(self.evaluate_object(obj, topology))
        return _build_health_report(results)

    def evaluate_case(self, case: Case) -> HealthReport:
        """Evaluate all voice objects attached to a case."""
        topology = TopologyBuilder().build(case.voice_objects)
        return self.evaluate_topology(topology)


def default_health_rule_registry() -> HealthRuleRegistry:
    """Create a registry preloaded with built-in rules."""
    registry = HealthRuleRegistry()
    register_builtin_rules(registry)
    return registry


def _build_health_report(results: list[HealthResult]) -> HealthReport:
    ordered = tuple(sorted(results, key=_result_sort_key))
    pass_count = sum(1 for result in ordered if result.status == HealthStatus.PASS)
    warn_count = sum(1 for result in ordered if result.status == HealthStatus.WARN)
    fail_count = sum(1 for result in ordered if result.status == HealthStatus.FAIL)

    category_counts = _count_by_category(ordered)
    severity_counts = _count_by_severity(ordered)
    recommendations = _build_recommendations(ordered)
    overall_score = _calculate_score(ordered)

    return HealthReport(
        overall_score=overall_score,
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        category_counts=category_counts,
        severity_counts=severity_counts,
        results=ordered,
        recommendations=recommendations,
    )


def _calculate_score(results: tuple[HealthResult, ...]) -> int:
    score = _BASE_SCORE
    for result in results:
        if result.status not in _ACTIVE_STATUSES:
            continue
        score -= _SEVERITY_PENALTIES.get(result.severity, 0)
    return max(score, 0)


def _count_by_category(results: tuple[HealthResult, ...]) -> tuple[tuple, ...]:
    counts: dict = {}
    for result in results:
        if result.status not in _ACTIVE_STATUSES:
            continue
        counts[result.category] = counts.get(result.category, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: item[0].value))


def _count_by_severity(results: tuple[HealthResult, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for result in results:
        if result.status not in _ACTIVE_STATUSES:
            continue
        key = result.severity.value
        counts[key] = counts.get(key, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: item[0]))


def _build_recommendations(results: tuple[HealthResult, ...]) -> tuple[str, ...]:
    recommendations: list[str] = []
    seen: set[str] = set()
    for result in results:
        if result.status not in _ACTIVE_STATUSES or not result.recommendation:
            continue
        if result.recommendation in seen:
            continue
        seen.add(result.recommendation)
        recommendations.append(result.recommendation)
    return tuple(recommendations)


def _result_sort_key(result: HealthResult) -> tuple[str, str, str]:
    return (result.object_id, result.rule_id, result.status.value)
