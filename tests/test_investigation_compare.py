"""Tests for the Investigation Comparison Engine."""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from cli.voicepilot_cli import main, run_compare_cases, run_compare_scenarios
from domain.enums import InvestigationState, Severity
from domain.models import AnalysisFinding, Case
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from investigation_compare import (
    ComparisonStatus,
    InvestigationComparisonEngine,
    READ_ONLY_NOTICE,
    format_comparison_markdown,
    snapshot_from_case,
)
from investigation_compare.compare_engine import InvestigationComparisonEngine as ICEngine
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_for_comparison,
)
from services import VoicePilotService
from services.service_models import ComparisonResult

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_ROOT = default_scenarios_root(VP_CUBE_0001_PLAYBOOK_ID, repo_root=REPO_ROOT)


def _case_with_findings(case_id: str, signals: tuple[str, ...], *, quality_score: int | None = None) -> Case:
    case = Case.create(
        title="Test case",
        symptom=SymptomSummary(summary="Outbound calls fail"),
        severity=Severity.HIGH,
        business_impact="Users cannot place outbound calls",
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        playbook_id=PLAYBOOK_ID,
    )
    case.case_id = case_id
    case.status = InvestigationState.INVESTIGATION
    case.analysis_findings = [
        AnalysisFinding.create(case_id, f"EVD-{index}", "show test", signal)
        for index, signal in enumerate(signals, start=1)
    ]
    if quality_score is not None:
        from investigation_quality.quality_models import InvestigationQualityReport, QualityMetricResult

        case.investigation_quality_report = InvestigationQualityReport(
            overall_score=quality_score,
            overall_status="PASS" if quality_score >= 80 else "WARN",
            metric_results=(
                QualityMetricResult(
                    metric_name="Evidence Coverage",
                    score=quality_score,
                    max_score=100,
                    status="PASS",
                    summary="Test metric",
                    recommendations=(),
                ),
            ),
            ready_for_recommendation=quality_score >= 80,
            ready_for_case_closure=False,
            generated_at=case.opened_at,
        )
    return case


PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID


@pytest.fixture
def sip_ua_pair():
    from runtime.scenario_runner import build_scenario_runtime_engine

    runtime = build_scenario_runtime_engine()
    try:
        _, before_id = run_scenario_for_comparison(
            SCENARIOS_ROOT / "sip_ua_disabled",
            runtime=runtime,
        )
        _, after_id = run_scenario_for_comparison(
            SCENARIOS_ROOT / "sip_ua_fixed",
            runtime=runtime,
        )
        yield runtime, before_id, after_id
    finally:
        runtime.shutdown()


class TestComparisonModels:
    def test_models_are_immutable(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_ua_disabled",))
        after = _case_with_findings("CASE-AFTER", ("sip_ua_enabled",))
        comparison = InvestigationComparisonEngine().compare_cases(before, after)
        with pytest.raises(dataclasses.FrozenInstanceError):
            comparison.status = ComparisonStatus.REGRESSED  # type: ignore[misc]


class TestInvestigationComparisonEngine:
    def test_improved_health_and_resolved_findings(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_ua_disabled", "dial_peer_down"))
        after = _case_with_findings("CASE-AFTER", ("sip_ua_enabled",))
        comparison = InvestigationComparisonEngine().compare_cases(before, after)

        assert comparison.status == ComparisonStatus.IMPROVED
        assert "sip_ua_disabled" in comparison.resolved_findings
        assert "dial_peer_down" in comparison.resolved_findings
        assert comparison.critical_findings_after == ()

    def test_improved_quality(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_503_detected",), quality_score=60)
        after = _case_with_findings("CASE-AFTER", ("sip_trace_present",), quality_score=85)
        comparison = InvestigationComparisonEngine().compare_cases(before, after)

        assert comparison.quality_before == 60
        assert comparison.quality_after == 85
        assert comparison.status in {ComparisonStatus.IMPROVED, ComparisonStatus.PARTIAL}

    def test_regression_detection(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_ua_enabled",))
        after = _case_with_findings("CASE-AFTER", ("sip_ua_disabled", "dial_peer_down"))
        comparison = InvestigationComparisonEngine().compare_cases(before, after)

        assert comparison.status == ComparisonStatus.REGRESSED
        assert comparison.new_findings

    def test_no_change(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_trace_present",), quality_score=80)
        after = _case_with_findings("CASE-AFTER", ("sip_trace_present",), quality_score=80)
        comparison = InvestigationComparisonEngine().compare_cases(before, after)

        assert comparison.status == ComparisonStatus.UNCHANGED
        assert not comparison.resolved_findings
        assert not comparison.new_findings

    def test_summary_generation(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_ua_disabled",))
        after = _case_with_findings("CASE-AFTER", ())
        engine = InvestigationComparisonEngine()
        comparison = engine.compare_cases(before, after)
        summary = engine.generate_summary(comparison)

        assert "IMPROVED" in summary
        assert comparison.before_case_id in summary

    def test_markdown_contains_required_sections(self) -> None:
        before = _case_with_findings("CASE-BEFORE", ("sip_ua_disabled",))
        after = _case_with_findings("CASE-AFTER", ())
        comparison = InvestigationComparisonEngine().compare_cases(before, after)
        markdown = format_comparison_markdown(comparison)

        for section in (
            "# Investigation Comparison",
            "## Executive Summary",
            "## Overall Status",
            "## Health",
            "## Confidence",
            "## Investigation Quality",
            "## Findings Resolved",
            "## Findings Remaining",
            "## New Findings",
            "## Verification",
            "## Overall Result",
            "## Read-Only Notice",
        ):
            assert section in markdown
        assert READ_ONLY_NOTICE in markdown

    def test_no_diagnosis_or_recommendation_logic(self) -> None:
        source = inspect.getsource(ICEngine)
        forbidden = (
            "HypothesisEngine(",
            "RecommendationEngine(",
            "AnalysisEngine(",
            "CorrelationEngine(",
        )
        for token in forbidden:
            assert token not in source


class TestScenarioComparison:
    def test_scenario_pair_shows_improvement(self, sip_ua_pair) -> None:
        runtime, before_id, after_id = sip_ua_pair
        comparison = runtime.compare_cases(before_id, after_id)

        assert comparison.status == ComparisonStatus.IMPROVED
        assert "sip_ua_disabled" in comparison.resolved_findings


class TestComparisonIntegration:
    def test_runtime_compare_cases(self, sip_ua_pair) -> None:
        runtime, before_id, after_id = sip_ua_pair
        comparison = runtime.compare_cases(before_id, after_id)
        assert comparison.comparison_id.startswith("CMP-")

    def test_service_compare_cases(self, sip_ua_pair) -> None:
        runtime, before_id, after_id = sip_ua_pair
        service = VoicePilotService(runtime_engine=runtime)
        result = service.compare_cases(before_id, after_id)

        assert isinstance(result, ComparisonResult)
        assert result.status == "IMPROVED"
        assert "# Investigation Comparison" in result.markdown


class TestComparisonCli:
    def test_cli_compare_scenarios(self, tmp_path: Path) -> None:
        output_path = tmp_path / "comparison.md"
        assert (
            main(
                [
                    "compare-scenarios",
                    PLAYBOOK_ID,
                    "sip_ua_disabled",
                    "sip_ua_fixed",
                    "--output",
                    str(output_path),
                ]
            )
            == 0
        )
        content = output_path.read_text(encoding="utf-8")
        assert READ_ONLY_NOTICE in content
        assert "IMPROVED" in content

    def test_cli_compare_scenarios_default_after_mapping(self) -> None:
        assert main(["compare-scenarios", PLAYBOOK_ID, "sip_ua_disabled"]) == 0

    def test_run_compare_scenarios_writes_output_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "cmp.md"
        output: list[str] = []
        code = run_compare_scenarios(
            PLAYBOOK_ID,
            "sip_ua_disabled",
            output.append,
            after_scenario="sip_ua_fixed",
            output_path=output_path,
            repo_root=REPO_ROOT,
        )
        assert code == 0
        assert output_path.exists()

    def test_run_compare_cases_not_found(self) -> None:
        output: list[str] = []
        code = run_compare_cases("CASE-missing-a", "CASE-missing-b", output.append)
        assert code == 1
