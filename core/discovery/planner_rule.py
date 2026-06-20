"""Discovery planner rule contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import Case
from discovery.planner_models import DiscoveryRequest


class DiscoveryPlannerRule(ABC):
    """Deterministic rule that recommends the next evidence to collect."""

    id: str
    title: str

    @abstractmethod
    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        """Return a discovery request when evidence is still needed."""
