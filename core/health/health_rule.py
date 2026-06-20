"""Base health rule contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from health.health_categories import HealthCategory
from health.health_models import HealthResult
from health.health_severity import HealthSeverity
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology


class HealthRule(ABC):
    """Deterministic vendor-neutral health rule."""

    id: str
    title: str
    description: str
    category: HealthCategory
    severity: HealthSeverity
    supported_object_types: tuple[str, ...]

    @abstractmethod
    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        """Evaluate the rule for a single object within a topology context."""
