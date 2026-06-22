"""Enterprise validation engine — validates investigations without performing them."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from change_package.change_models import EngineeringChangePackage
from domain.models import Case, Hypothesis
from engineering_knowledge import default_engineering_knowledge_engine
from health.health_engine import HealthEngine
from infrastructure.yaml_loader import YamlLoader
from reporting.report_models import ReportType
from runtime.scenario_runner import (
    build_scenario_runtime_engine,
    default_repo_root,
    default_scenarios_root,
    discover_scenario_dirs,
    resolve_scenario_dirs,
    run_scenario_to_correlation,
)
from validation.validation_models import (
    ScenarioExpectation,
    ValidationMetrics,
    ValidationResult,
    ValidationScenario,
    ValidationSuite,
    ValidationSummary,
)
from validation.validation_rules import evaluate_expectations

SUPPORTED_VALIDATION_PLAYBOOKS: tuple[str, ...] = (
    "VP-CUBE-0001",
    "VP-CUCM-0001",
    "VP-TEAMS-0001",
)


class UnsupportedValidationPlaybookError(ValueError):
    """Raised when a playbook is not part of the validation suite."""


class ValidationEngine:
    """Run existing investigations and validate deterministic outcomes."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        plugins_root: Path | None = None,
    ) -> None:
        self._repo_root = repo_root or default_repo_root()
        self._plugins_root = plugins_root

    def discover_scenarios(self, playbook_id: str) -> tuple[ValidationScenario, ...]:
        """Return validation scenarios for a supported playbook."""
        self._ensure_supported_playbook(playbook_id)
        scenarios_root = default_scenarios_root(playbook_id, repo_root=self._repo_root)
        return tuple(
            ValidationScenario(
                scenario_id=path.name,
                playbook_id=playbook_id,
                scenario_dir=path,
                expectation=load_scenario_expectation(path),
            )
            for path in discover_scenario_dirs(scenarios_root)
        )

    def validate_scenario(
        self,
        scenario_dir: Path,
        playbook_id: str,
    ) -> ValidationResult:
        """Run one scenario through the investigation pipeline and validate outputs."""
        self._ensure_supported_playbook(playbook_id)
        expectation = load_scenario_expectation(scenario_dir)
        started = time.perf_counter()
        runtime = build_scenario_runtime_engine(self._plugins_root)

        try:
            case_id = self._run_investigation_pipeline(runtime, scenario_dir, playbook_id)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            case = runtime.case_manager.load_case(case_id)
            top_hypothesis = _top_hypothesis(case)
            actual_root_cause = top_hypothesis.title if top_hypothesis else None
            confidence = float(top_hypothesis.confidence) if top_hypothesis else 0.0

            health_report = HealthEngine().evaluate_case(case) if case.voice_objects else None
            knowledge_report = default_engineering_knowledge_engine().evaluate_case(case)
            quality_report = case.investigation_quality_report
            change_package = case.change_package
            report = runtime.generate_report(case_id, ReportType.ENGINEERING)
            discovery_plan = runtime.plan_discovery(case_id)

            metrics = ValidationMetrics(
                execution_time_ms=elapsed_ms,
                confidence=confidence,
                investigation_quality_score=(
                    quality_report.overall_score if quality_report is not None else None
                ),
                knowledge_match_count=len(knowledge_report.matches),
                health_score=health_report.overall_score if health_report is not None else None,
                report_size_bytes=len(report.markdown.encode("utf-8")),
                topology_object_count=len(case.voice_objects),
                discovery_command_count=len(discovery_plan.requests),
                critical_finding_signals=tuple(
                    sorted(
                        {
                            finding.signal
                            for finding in case.analysis_findings
                            if finding.signal
                        }
                    )
                ),
            )

            passed, failure_reasons = evaluate_expectations(
                expectation,
                actual_root_cause=actual_root_cause,
                confidence=confidence,
                case=case,
                health_report=health_report,
                knowledge_report=knowledge_report,
                quality_report=quality_report,
                change_package=change_package,
                report_markdown=report.markdown,
                metrics=metrics,
            )
            return ValidationResult(
                scenario_id=expectation.scenario_id,
                playbook_id=playbook_id,
                passed=passed,
                failure_reasons=failure_reasons,
                expectation=expectation,
                actual_root_cause=actual_root_cause,
                metrics=metrics,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return ValidationResult(
                scenario_id=expectation.scenario_id,
                playbook_id=playbook_id,
                passed=False,
                failure_reasons=(str(exc),),
                expectation=expectation,
                actual_root_cause=None,
                metrics=_empty_metrics(elapsed_ms),
                error=str(exc),
            )
        finally:
            runtime.shutdown()

    def validate_playbook(self, playbook_id: str) -> ValidationSuite:
        """Validate every scenario for one playbook."""
        scenarios = resolve_scenario_dirs(playbook_id, repo_root=self._repo_root)
        results = tuple(
            self.validate_scenario(scenario_dir, playbook_id) for scenario_dir in scenarios
        )
        return ValidationSuite(
            summary=_build_summary(results, playbook_id),
            results=results,
            generated_at=datetime.now(timezone.utc),
        )

    def validate_all(self) -> ValidationSuite:
        """Validate scenarios for every supported playbook."""
        results: list[ValidationResult] = []
        for playbook_id in SUPPORTED_VALIDATION_PLAYBOOKS:
            suite = self.validate_playbook(playbook_id)
            results.extend(suite.results)
        combined = tuple(results)
        return ValidationSuite(
            summary=_build_summary(combined, None),
            results=combined,
            generated_at=datetime.now(timezone.utc),
        )

    def _run_investigation_pipeline(
        self,
        runtime,
        scenario_dir: Path,
        playbook_id: str,
    ) -> str:
        """Execute the existing runtime pipeline through report generation."""
        _, case_id = run_scenario_to_correlation(
            scenario_dir,
            playbook_id=playbook_id,
            runtime=runtime,
        )
        runtime.generate_recommendation(case_id)
        runtime.evaluate_investigation_quality(case_id)
        runtime.generate_change_package(case_id)
        runtime.plan_discovery(case_id)
        return case_id

    def _ensure_supported_playbook(self, playbook_id: str) -> None:
        if playbook_id not in SUPPORTED_VALIDATION_PLAYBOOKS:
            raise UnsupportedValidationPlaybookError(
                f"Unsupported validation playbook: {playbook_id}. "
                f"Supported: {', '.join(SUPPORTED_VALIDATION_PLAYBOOKS)}"
            )


def load_scenario_expectation(scenario_dir: Path) -> ScenarioExpectation:
    """Load scenario expectations from ``expected_result.yaml``."""
    data = YamlLoader().load_file(scenario_dir / "expected_result.yaml")
    return ScenarioExpectation(
        scenario_id=str(data.get("scenario_id", scenario_dir.name)),
        expected_root_cause=str(data["expected_root_cause"]),
        min_confidence=float(data.get("min_confidence", 0)),
        expected_root_cause_aliases=tuple(data.get("expected_root_cause_aliases", [])),
        expected_health_status=data.get("expected_health_status"),
        expected_critical_findings=tuple(data.get("expected_critical_findings", [])),
        expected_knowledge_ids=tuple(data.get("expected_knowledge_ids", [])),
        expected_runbook_ids=tuple(data.get("expected_runbook_ids", [])),
        expected_verification_ids=tuple(data.get("expected_verification_ids", [])),
        require_change_package=bool(data.get("require_change_package", True)),
        require_report=bool(data.get("require_report", True)),
        require_recommendation=bool(data.get("require_recommendation", True)),
        min_quality_score=data.get("min_quality_score"),
        min_health_score=data.get("min_health_score"),
    )


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _empty_metrics(execution_time_ms: float) -> ValidationMetrics:
    return ValidationMetrics(
        execution_time_ms=execution_time_ms,
        confidence=0.0,
        investigation_quality_score=None,
        knowledge_match_count=0,
        health_score=None,
        report_size_bytes=0,
        topology_object_count=0,
        discovery_command_count=0,
        critical_finding_signals=(),
    )


def _build_summary(
    results: tuple[ValidationResult, ...],
    playbook_id: str | None,
) -> ValidationSummary:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed
    confidences = [result.metrics.confidence for result in results]
    qualities = [
        result.metrics.investigation_quality_score
        for result in results
        if result.metrics.investigation_quality_score is not None
    ]
    execution_times = [result.metrics.execution_time_ms for result in results]

    fastest_id: str | None = None
    fastest_ms: float | None = None
    slowest_id: str | None = None
    slowest_ms: float | None = None
    if results:
        fastest = min(results, key=lambda result: result.metrics.execution_time_ms)
        slowest = max(results, key=lambda result: result.metrics.execution_time_ms)
        fastest_id = fastest.scenario_id
        fastest_ms = fastest.metrics.execution_time_ms
        slowest_id = slowest.scenario_id
        slowest_ms = slowest.metrics.execution_time_ms

    return ValidationSummary(
        playbook_id=playbook_id,
        total_scenarios=total,
        passed_count=passed,
        failed_count=failed,
        accuracy_percent=(passed / total * 100.0) if total else 0.0,
        average_confidence=(sum(confidences) / len(confidences)) if confidences else 0.0,
        average_quality=(sum(qualities) / len(qualities)) if qualities else None,
        total_execution_time_ms=sum(execution_times),
        average_execution_time_ms=(sum(execution_times) / len(execution_times))
        if execution_times
        else 0.0,
        fastest_scenario_id=fastest_id,
        fastest_execution_time_ms=fastest_ms,
        slowest_scenario_id=slowest_id,
        slowest_execution_time_ms=slowest_ms,
    )
