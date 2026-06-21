"""Tests for the enterprise validation suite."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from change_package.change_models import EngineeringChangePackage
from change_package.change_risk import ChangeRiskLevel
from cli.voicepilot_cli import main, run_validation
from domain.enums import Severity
from domain.models import Case, Hypothesis, Recommendation
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.scenario_runner import VP_CUBE_0001_PLAYBOOK_ID, default_scenarios_root
from validation import (
    SUPPORTED_VALIDATION_PLAYBOOKS,
    ScenarioExpectation,
    ValidationEngine,
    ValidationMetrics,
    ValidationSuite,
    ValidationSummary,
    evaluate_expectations,
    format_validation_report,
    format_validation_summary_line,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CUBE_SCENARIOS_ROOT = default_scenarios_root(VP_CUBE_0001_PLAYBOOK_ID, repo_root=REPO_ROOT)


@pytest.fixture
def validation_engine() -> ValidationEngine:
    return ValidationEngine(repo_root=REPO_ROOT)


def _sample_case(*, recommendations: list[Recommendation] | None = None) -> Case:
    case = Case.create(
        title="Validation test",
        symptom=SymptomSummary(summary="test"),
        severity=Severity.MEDIUM,
        business_impact="test",
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="Cisco", products=("CUBE",)),
        playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
    )
    case.recommendations.extend(recommendations or [])
    return case


def _sample_change_package(case: Case) -> EngineeringChangePackage:
    return EngineeringChangePackage(
        package_id="PKG-test",
        case_id=case.case_id,
        playbook_id=case.playbook_id,
        generated_at=datetime.now(timezone.utc),
        title="Test package",
        executive_summary="Advisory summary",
        root_cause="Test root cause",
        confidence=90.0,
        evidence_reviewed=("show sip-ua status",),
        affected_components=("Cisco CUBE",),
        recommended_changes=(),
        configuration_examples=(),
        rollback_examples=(),
        verification_steps=(),
        post_change_validation=(),
        risk_level=ChangeRiskLevel.MEDIUM,
        risk_summary="Medium risk",
        prerequisites=(),
        assumptions=(),
        related_knowledge_assets=("VP-CISCO-CUCM-RB-001",),
        vendor_references=(),
        approval_sections=(),
        engineer_notes=(),
    )


class TestValidationEngine:
    def test_supported_playbooks(self) -> None:
        assert "VP-CUBE-0001" in SUPPORTED_VALIDATION_PLAYBOOKS
        assert "VP-CUCM-0001" in SUPPORTED_VALIDATION_PLAYBOOKS

    def test_discover_cube_scenarios(self, validation_engine: ValidationEngine) -> None:
        scenarios = validation_engine.discover_scenarios(VP_CUBE_0001_PLAYBOOK_ID)
        scenario_ids = {scenario.scenario_id for scenario in scenarios}
        assert "sip_ua_disabled" in scenario_ids
        assert len(scenarios) == 5

    def test_validate_cube_playbook_passes(self, validation_engine: ValidationEngine) -> None:
        suite = validation_engine.validate_playbook(VP_CUBE_0001_PLAYBOOK_ID)
        assert suite.summary.total_scenarios == 5
        assert suite.summary.failed_count == 0
        assert suite.summary.accuracy_percent == 100.0

    def test_validate_cucm_playbook_passes(self, validation_engine: ValidationEngine) -> None:
        suite = validation_engine.validate_playbook("VP-CUCM-0001")
        assert suite.summary.total_scenarios == 5
        assert suite.summary.failed_count == 0

    def test_validate_all_playbooks(self, validation_engine: ValidationEngine) -> None:
        suite = validation_engine.validate_all()
        assert suite.summary.total_scenarios == 10
        assert suite.summary.playbook_id is None
        assert suite.summary.failed_count == 0

    def test_metrics_captured_for_scenario(self, validation_engine: ValidationEngine) -> None:
        scenario_dir = CUBE_SCENARIOS_ROOT / "sip_ua_disabled"
        result = validation_engine.validate_scenario(scenario_dir, VP_CUBE_0001_PLAYBOOK_ID)
        assert result.metrics.execution_time_ms > 0
        assert result.metrics.confidence >= 98
        assert result.metrics.report_size_bytes > 0
        assert result.metrics.topology_object_count >= 0
        assert result.metrics.discovery_command_count >= 0
        assert result.metrics.knowledge_match_count >= 0

    def test_performance_summary_tracks_fastest_and_slowest(
        self, validation_engine: ValidationEngine
    ) -> None:
        suite = validation_engine.validate_playbook(VP_CUBE_0001_PLAYBOOK_ID)
        assert suite.summary.fastest_scenario_id is not None
        assert suite.summary.slowest_scenario_id is not None
        assert suite.summary.total_execution_time_ms > 0
        assert suite.summary.average_execution_time_ms > 0


class TestValidationRegression:
    def test_fails_on_wrong_root_cause(self) -> None:
        expectation = ScenarioExpectation(
            scenario_id="test",
            expected_root_cause="Expected cause",
            min_confidence=80,
        )
        case = _sample_case()
        passed, failures = evaluate_expectations(
            expectation,
            actual_root_cause="Different cause",
            confidence=95.0,
            case=case,
            health_report=None,
            knowledge_report=None,
            quality_report=None,
            change_package=_sample_change_package(case),
            report_markdown="# Report",
            metrics=_metrics(confidence=95.0),
        )
        assert not passed
        assert any("Root cause mismatch" in reason for reason in failures)

    def test_fails_on_low_confidence(self) -> None:
        expectation = ScenarioExpectation(
            scenario_id="test",
            expected_root_cause="Expected cause",
            min_confidence=90,
        )
        case = _sample_case()
        passed, failures = evaluate_expectations(
            expectation,
            actual_root_cause="Expected cause",
            confidence=70.0,
            case=case,
            health_report=None,
            knowledge_report=None,
            quality_report=None,
            change_package=_sample_change_package(case),
            report_markdown="# Report",
            metrics=_metrics(confidence=70.0),
        )
        assert not passed
        assert any("Confidence" in reason for reason in failures)

    def test_fails_on_missing_recommendation(self) -> None:
        expectation = ScenarioExpectation(
            scenario_id="test",
            expected_root_cause="Expected cause",
            min_confidence=80,
            require_recommendation=True,
        )
        case = _sample_case(recommendations=[])
        passed, failures = evaluate_expectations(
            expectation,
            actual_root_cause="Expected cause",
            confidence=95.0,
            case=case,
            health_report=None,
            knowledge_report=None,
            quality_report=None,
            change_package=_sample_change_package(case),
            report_markdown="# Report",
            metrics=_metrics(confidence=95.0),
        )
        assert not passed
        assert "Missing recommendation" in failures

    def test_fails_on_missing_report(self) -> None:
        expectation = ScenarioExpectation(
            scenario_id="test",
            expected_root_cause="Expected cause",
            min_confidence=80,
            require_report=True,
        )
        case = _sample_case()
        case.recommendations.append(
            Recommendation.create(
                case_id=case.case_id,
                action_type=ACTION_LIKELY_ROOT_CAUSE,
                description="Likely root cause",
                rationale="Evidence supports root cause",
                confidence=95.0,
                likely_root_cause="Expected cause",
            )
        )
        passed, failures = evaluate_expectations(
            expectation,
            actual_root_cause="Expected cause",
            confidence=95.0,
            case=case,
            health_report=None,
            knowledge_report=None,
            quality_report=None,
            change_package=_sample_change_package(case),
            report_markdown="",
            metrics=_metrics(confidence=95.0),
        )
        assert not passed
        assert "Missing report output" in failures

    def test_fails_on_missing_knowledge_id(self) -> None:
        from engineering_knowledge.knowledge_models import KnowledgeReport

        expectation = ScenarioExpectation(
            scenario_id="test",
            expected_root_cause="Expected cause",
            min_confidence=80,
            expected_knowledge_ids=("VP-KNOW-001",),
        )
        case = _sample_case()
        knowledge_report = KnowledgeReport(
            matches=(),
            related_assets=(),
            recommendations=(),
            summary="No matches",
        )
        passed, failures = evaluate_expectations(
            expectation,
            actual_root_cause="Expected cause",
            confidence=95.0,
            case=case,
            health_report=None,
            knowledge_report=knowledge_report,
            quality_report=None,
            change_package=_sample_change_package(case),
            report_markdown="# Report",
            metrics=_metrics(confidence=95.0),
        )
        assert not passed
        assert any("knowledge ID" in reason for reason in failures)


class TestValidationReport:
    def test_markdown_contains_required_sections(self) -> None:
        suite = ValidationSuite(
            summary=ValidationSummary(
                playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
                total_scenarios=1,
                passed_count=1,
                failed_count=0,
                accuracy_percent=100.0,
                average_confidence=98.0,
                average_quality=85.0,
                total_execution_time_ms=120.0,
                average_execution_time_ms=120.0,
                fastest_scenario_id="sip_ua_disabled",
                fastest_execution_time_ms=120.0,
                slowest_scenario_id="sip_ua_disabled",
                slowest_execution_time_ms=120.0,
            ),
            results=(),
            generated_at=datetime.now(timezone.utc),
        )
        markdown = format_validation_report(suite)
        assert "# VoicePilot Validation Report" in markdown
        assert "## Summary" in markdown
        assert "## Scenario Results" in markdown
        assert "## Performance" in markdown
        assert "VP-CUBE-0001" in markdown

    def test_summary_line(self) -> None:
        suite = ValidationSuite(
            summary=ValidationSummary(
                playbook_id=None,
                total_scenarios=10,
                passed_count=10,
                failed_count=0,
                accuracy_percent=100.0,
                average_confidence=90.0,
                average_quality=80.0,
                total_execution_time_ms=1000.0,
                average_execution_time_ms=100.0,
                fastest_scenario_id="a",
                fastest_execution_time_ms=50.0,
                slowest_scenario_id="b",
                slowest_execution_time_ms=200.0,
            ),
            results=(),
            generated_at=datetime.now(timezone.utc),
        )
        assert "10 passed" in format_validation_summary_line(suite)


class TestValidationCli:
    def test_cli_validate_cube_playbook(self) -> None:
        assert main(["validate", VP_CUBE_0001_PLAYBOOK_ID]) == 0

    def test_cli_validate_cucm_playbook(self) -> None:
        assert main(["validate", "VP-CUCM-0001"]) == 0

    def test_cli_validate_all_playbooks(self) -> None:
        assert main(["validate"]) == 0

    def test_cli_validate_writes_output_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "validation.md"
        assert (
            run_validation(
                VP_CUBE_0001_PLAYBOOK_ID,
                lambda *_args, **_kwargs: None,
                output_path=output_path,
            )
            == 0
        )
        assert output_path.is_file()
        assert "# VoicePilot Validation Report" in output_path.read_text(encoding="utf-8")


def _metrics(*, confidence: float) -> ValidationMetrics:
    return ValidationMetrics(
        execution_time_ms=10.0,
        confidence=confidence,
        investigation_quality_score=85,
        knowledge_match_count=1,
        health_score=70,
        report_size_bytes=100,
        topology_object_count=2,
        discovery_command_count=1,
        critical_finding_signals=("sip_ua_disabled",),
    )
