"""Health severity levels for rule evaluation."""

from __future__ import annotations

from enum import Enum


class HealthSeverity(str, Enum):
    """Severity assigned to a health rule or finding."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
