"""Deterministic discovery planning engine."""

from __future__ import annotations

from domain.enums import HypothesisStatus
from domain.models import Case
from discovery.planner_bootstrap import default_discovery_registry
from discovery.planner_models import DiscoveryPlan, DiscoveryRequest
from discovery.planner_registry import DiscoveryPlannerRegistry

_MAX_CONFIDENCE = 100.0


class PlannerEngine:
    """Recommend next evidence to collect based on investigation state."""

    def __init__(self, registry: DiscoveryPlannerRegistry | None = None) -> None:
        self._registry = registry or default_discovery_registry()

    @property
    def registry(self) -> DiscoveryPlannerRegistry:
        """Return the planner registry."""
        return self._registry

    def evaluate_case(self, case: Case) -> DiscoveryPlan:
        """Produce a ranked discovery plan for the case."""
        raw_requests = self._registry.evaluate(case)
        pending = [
            request.with_score()
            for request in raw_requests
            if not request.already_collected
        ]
        deduped = _dedupe_by_command(pending)
        ranked = tuple(
            sorted(
                deduped,
                key=lambda item: (-item.score, item.command, item.request_id),
            )
        )

        current_confidence = _current_confidence(case)
        total_gain = sum(request.estimated_confidence_gain for request in ranked)
        estimated_final_confidence = min(_MAX_CONFIDENCE, current_confidence + total_gain)
        remaining_uncertainty = max(0.0, _MAX_CONFIDENCE - current_confidence)
        next_best_command = ranked[0].command if ranked else None
        total_estimated_minutes = sum(request.estimated_minutes for request in ranked)

        return DiscoveryPlan(
            requests=ranked,
            current_confidence=current_confidence,
            estimated_final_confidence=estimated_final_confidence,
            remaining_uncertainty=remaining_uncertainty,
            next_best_command=next_best_command,
            total_estimated_minutes=total_estimated_minutes,
        )


def _current_confidence(case: Case) -> float:
    if not case.hypotheses:
        return 0.0
    active = [
        hypothesis
        for hypothesis in case.hypotheses
        if hypothesis.status != HypothesisStatus.ELIMINATED
    ]
    if not active:
        return 0.0
    top = min(active, key=lambda item: item.rank or 999)
    return top.confidence


def _dedupe_by_command(requests: list[DiscoveryRequest]) -> list[DiscoveryRequest]:
    """Keep the highest-scoring request for each command."""
    best_by_command: dict[str, DiscoveryRequest] = {}
    for request in requests:
        existing = best_by_command.get(request.command)
        if existing is None or request.score > existing.score:
            best_by_command[request.command] = request
    return list(best_by_command.values())
