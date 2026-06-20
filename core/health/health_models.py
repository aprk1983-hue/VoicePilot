"""Core health evaluation result models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from health.health_categories import HealthCategory
from health.health_severity import HealthSeverity


class HealthStatus(str, Enum):
    """Outcome of a health rule evaluation."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthResult:
    """Result of evaluating one health rule against one object."""

    rule_id: str
    title: str
    description: str
    category: HealthCategory
    severity: HealthSeverity
    status: HealthStatus
    object_id: str
    object_type: str
    message: str
    recommendation: str | None = None
