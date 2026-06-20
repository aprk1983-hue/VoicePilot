"""Bootstrap helpers for the investigation quality framework."""

from __future__ import annotations

from investigation_quality.builtin_metrics import register_builtin_metrics
from investigation_quality.quality_registry import InvestigationQualityRegistry


def default_quality_registry() -> InvestigationQualityRegistry:
    """Create a registry preloaded with built-in quality metrics."""
    registry = InvestigationQualityRegistry()
    register_builtin_metrics(registry)
    return registry
