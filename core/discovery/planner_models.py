"""Discovery planner domain models."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class DiscoveryPriority(str, Enum):
    """Relative urgency for collecting investigative evidence."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


PRIORITY_WEIGHTS: dict[DiscoveryPriority, float] = {
    DiscoveryPriority.CRITICAL: 100.0,
    DiscoveryPriority.HIGH: 75.0,
    DiscoveryPriority.MEDIUM: 50.0,
    DiscoveryPriority.LOW: 25.0,
}


@dataclass(frozen=True)
class DiscoveryRequest:
    """Recommended evidence collection action for an investigation."""

    request_id: str
    command: str
    vendor: str
    priority: DiscoveryPriority
    reason: str
    estimated_confidence_gain: float
    estimated_minutes: int
    related_hypotheses: tuple[str, ...]
    already_collected: bool
    optional: bool
    score: float = 0.0

    def with_score(self) -> DiscoveryRequest:
        """Return a copy with the deterministic planner score applied."""
        return replace(self, score=compute_discovery_score(self))


@dataclass(frozen=True)
class DiscoveryPlan:
    """Immutable ranked plan of recommended evidence collection."""

    requests: tuple[DiscoveryRequest, ...]
    current_confidence: float
    estimated_final_confidence: float
    remaining_uncertainty: float
    next_best_command: str | None
    total_estimated_minutes: int


def compute_discovery_score(request: DiscoveryRequest) -> float:
    """Compute deterministic planner score for a discovery request."""
    return (
        PRIORITY_WEIGHTS[request.priority]
        + request.estimated_confidence_gain
        + float(len(request.related_hypotheses))
    )
