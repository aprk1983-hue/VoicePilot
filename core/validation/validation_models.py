"""Immutable models for the enterprise validation suite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ScenarioExpectation:
    """Expected outcomes for a validation scenario."""

    scenario_id: str
    expected_root_cause: str
    min_confidence: float
    expected_root_cause_aliases: tuple[str, ...] = ()
    expected_health_status: str | None = None
    expected_critical_findings: tuple[str, ...] = ()
    expected_knowledge_ids: tuple[str, ...] = ()
    expected_runbook_ids: tuple[str, ...] = ()
    expected_verification_ids: tuple[str, ...] = ()
    require_change_package: bool = True
    require_report: bool = True
    require_recommendation: bool = True
    min_quality_score: int | None = None
    min_health_score: int | None = None


@dataclass(frozen=True)
class ValidationMetrics:
    """Captured measurements for one validated scenario."""

    execution_time_ms: float
    confidence: float
    investigation_quality_score: int | None
    knowledge_match_count: int
    health_score: int | None
    report_size_bytes: int
    topology_object_count: int
    discovery_command_count: int
    critical_finding_signals: tuple[str, ...]


@dataclass(frozen=True)
class ValidationScenario:
    """A discoverable scenario with expectations."""

    scenario_id: str
    playbook_id: str
    scenario_dir: Path
    expectation: ScenarioExpectation


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of validating one scenario investigation."""

    scenario_id: str
    playbook_id: str
    passed: bool
    failure_reasons: tuple[str, ...]
    expectation: ScenarioExpectation
    actual_root_cause: str | None
    metrics: ValidationMetrics
    error: str | None = None


@dataclass(frozen=True)
class ValidationSummary:
    """Aggregated validation statistics."""

    playbook_id: str | None
    total_scenarios: int
    passed_count: int
    failed_count: int
    accuracy_percent: float
    average_confidence: float
    average_quality: float | None
    total_execution_time_ms: float
    average_execution_time_ms: float
    fastest_scenario_id: str | None
    fastest_execution_time_ms: float | None
    slowest_scenario_id: str | None
    slowest_execution_time_ms: float | None


@dataclass(frozen=True)
class ValidationSuite:
    """Complete validation run for one or more playbooks."""

    summary: ValidationSummary
    results: tuple[ValidationResult, ...]
    generated_at: datetime
