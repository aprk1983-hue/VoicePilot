"""Registry for investigation quality metrics."""

from __future__ import annotations

from domain.models import Case
from investigation_quality.quality_metric import InvestigationQualityMetric
from investigation_quality.quality_models import QualityMetricResult


class DuplicateQualityMetricError(Exception):
    """Raised when registering a metric with an existing name."""

    def __init__(self, metric_name: str) -> None:
        self.metric_name = metric_name
        super().__init__(f"Investigation quality metric already registered: {metric_name}")


class InvestigationQualityRegistry:
    """Register and evaluate investigation quality metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, InvestigationQualityMetric] = {}

    def register_metric(self, metric: InvestigationQualityMetric) -> None:
        """Register a metric, preventing duplicate names."""
        if metric.name in self._metrics:
            raise DuplicateQualityMetricError(metric.name)
        self._metrics[metric.name] = metric

    def get(self, metric_name: str) -> InvestigationQualityMetric | None:
        """Return a metric by name."""
        return self._metrics.get(metric_name)

    def all_metrics(self) -> tuple[InvestigationQualityMetric, ...]:
        """Return all registered metrics in deterministic order."""
        return tuple(sorted(self._metrics.values(), key=lambda item: item.name))

    def evaluate(self, case: Case) -> tuple[QualityMetricResult, ...]:
        """Evaluate all metrics and return results in deterministic order."""
        results: list[QualityMetricResult] = []
        for metric in self.all_metrics():
            results.append(metric.evaluate(case))
        return tuple(results)
