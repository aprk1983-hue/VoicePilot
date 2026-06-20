"""Vendor-neutral health evaluation framework."""

from health.health_categories import HealthCategory
from health.health_engine import HealthEngine, default_health_rule_registry
from health.health_models import HealthResult, HealthStatus
from health.health_report import HealthReport
from health.health_rule import HealthRule
from health.health_rule_registry import DuplicateHealthRuleError, HealthRuleRegistry
from health.health_severity import HealthSeverity

__all__ = [
    "DuplicateHealthRuleError",
    "HealthCategory",
    "HealthEngine",
    "HealthReport",
    "HealthResult",
    "HealthRule",
    "HealthRuleRegistry",
    "HealthSeverity",
    "HealthStatus",
    "default_health_rule_registry",
]
