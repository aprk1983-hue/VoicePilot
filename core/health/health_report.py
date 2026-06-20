"""Aggregated health evaluation report."""

from __future__ import annotations

from dataclasses import dataclass, field

from health.health_categories import HealthCategory
from health.health_models import HealthResult


@dataclass(frozen=True)
class HealthReport:
    """Aggregated health evaluation for objects or a full topology."""

    overall_score: int
    pass_count: int
    warn_count: int
    fail_count: int
    category_counts: tuple[tuple[HealthCategory, int], ...]
    severity_counts: tuple[tuple[str, int], ...]
    results: tuple[HealthResult, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)
