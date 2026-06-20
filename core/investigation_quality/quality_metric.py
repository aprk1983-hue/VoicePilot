"""Investigation quality metric contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import Case
from investigation_quality.quality_models import QualityMetricResult


class InvestigationQualityMetric(ABC):
    """Deterministic vendor-neutral investigation quality metric."""

    name: str
    title: str

    @abstractmethod
    def evaluate(self, case: Case) -> QualityMetricResult:
        """Evaluate investigation quality for a case."""
