"""Tests for the investigation quality framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case, Evidence
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from discovery.planner_engine import PlannerEngine
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from investigation_quality import (
    DuplicateQualityMetricError,
    InvestigationQualityEngine,
    InvestigationQualityMetric,
    InvestigationQualityRegistry,
    InvestigationQualityReport,
    QualityMetricResult,
    QualityStatus,
    format_investigation_quality_markdown,
    format_investigation_quality_report_section,
)
from investigation_quality.builtin_metrics import (
    EVIDENCE_COMPLETENESS_METRIC_NAME,
    EvidenceCompletenessMetric,
)
from runtime.exceptions import CaseNotFoundError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.report_engine import build_incident_report, format_incident_report
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import (
    EVIDENCE_FILES,
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=PLUGINS_ROOT.parent)
PARTIAL_EVIDENCE_FILES = EVIDENCE_FILES[:2]
VOICE_SERVICE_ONLY = (EVIDENCE_FILES[2],)
ONE_CRITICAL_MISSING_FILES = EVIDENCE_FILES[:2]


def _case(**kwargs) -> Case:
    status = kwargs.pop("status", InvestigationState.INVESTIGATION)
    case = Case.create(
        title="Outbound calls fail",
        symptom=SymptomSummary(summary="PSTN outbound failure"),
        severity=Severity.HIGH,
        business_impact="Users cannot place outbound calls",
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        **kwargs,
    )
    case.status = status
    return case


def _evidence(case_id: str, command: str) -> Evidence:
    return Evidence.create_cli_paste(case_id, command, "sample output")


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


class TestInvestigationQualityModels:
    def test_quality_metric_result_is_immutable(self) -> None:
        result = QualityMetricResult(
            metric_name="evidence_completeness",
            score=75,
            max_score=100,
            status=QualityStatus.WARN,
            summary="One critical evidence item is missing.",
            recommendations=("Collect missing evidence: `debug ccsip messages`",),
        )

        with pytest.raises(FrozenInstanceError):
            result.score = 100  # type: ignore[misc]

    def test_investigation_quality_report_is_immutable(self) -> None:
        report = InvestigationQualityReport(
            overall_score=75,
            overall_status=QualityStatus.WARN,
            metric_results=(),
            ready_for_recommendation=True,
            ready_for_case_closure=False,
            generated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(FrozenInstanceError):
            report.overall_score = 100  # type: ignore[misc]


class TestInvestigationQualityRegistry:
    def test_duplicate_metric_rejection(self) -> None:
        registry = InvestigationQualityRegistry()
        registry.register_metric(EvidenceCompletenessMetric())
        with pytest.raises(DuplicateQualityMetricError):
            registry.register_metric(EvidenceCompletenessMetric())

    def test_evaluate_returns_metrics_in_name_order(self) -> None:
        registry = InvestigationQualityRegistry()

        @dataclass(frozen=True)
        class ZuluMetric(InvestigationQualityMetric):
            name: str = "zulu_metric"
            title: str = "Zulu"

            def evaluate(self, case: Case) -> QualityMetricResult:
                return QualityMetricResult(
                    metric_name=self.name,
                    score=10,
                    max_score=100,
                    status=QualityStatus.FAIL,
                    summary="Zulu",
                    recommendations=(),
                )

        @dataclass(frozen=True)
        class AlphaMetric(InvestigationQualityMetric):
            name: str = "alpha_metric"
            title: str = "Alpha"

            def evaluate(self, case: Case) -> QualityMetricResult:
                return QualityMetricResult(
                    metric_name=self.name,
                    score=90,
                    max_score=100,
                    status=QualityStatus.PASS,
                    summary="Alpha",
                    recommendations=(),
                )

        registry.register_metric(ZuluMetric())
        registry.register_metric(AlphaMetric())

        results = registry.evaluate(_case())
        assert [result.metric_name for result in results] == ["alpha_metric", "zulu_metric"]


class TestEvidenceCompletenessMetric:
    def test_empty_investigation_scores_zero(self) -> None:
        metric = EvidenceCompletenessMetric()
        result = metric.evaluate(_case())

        assert result.metric_name == EVIDENCE_COMPLETENESS_METRIC_NAME
        assert result.score == 0
        assert result.status == QualityStatus.FAIL
        assert "No investigative evidence" in result.summary
        assert result.recommendations

    def test_all_evidence_collected_scores_one_hundred(self) -> None:
        case = _case(
            evidence=[
                _evidence("CASE-1", "show dial-peer voice summary"),
                _evidence("CASE-1", "show sip-ua status"),
                _evidence("CASE-1", "show run | sec voice service voip"),
                _evidence("CASE-1", "debug ccsip messages"),
            ],
        )
        case.discovery_plan = PlannerEngine().evaluate_case(case)

        result = EvidenceCompletenessMetric().evaluate(case)

        assert result.score == 100
        assert result.status == QualityStatus.PASS
        assert result.recommendations == ()

    def test_one_critical_missing_scores_seventy_five(self) -> None:
        case = _case(
            evidence=[
                _evidence("CASE-2", command)
                for command, _filename in ONE_CRITICAL_MISSING_FILES
            ],
        )
        case.discovery_plan = PlannerEngine().evaluate_case(case)

        result = EvidenceCompletenessMetric().evaluate(case)

        assert result.score == 75
        assert result.status == QualityStatus.WARN
        assert "One critical evidence item is missing" in result.summary
        assert any(
            "show run | sec voice service voip" in item for item in result.recommendations
        )

    def test_multiple_critical_missing_scores_fifty(self) -> None:
        case = _case(
            evidence=[_evidence("CASE-3", VOICE_SERVICE_ONLY[0][0])],
        )
        case.discovery_plan = PlannerEngine().evaluate_case(case)

        result = EvidenceCompletenessMetric().evaluate(case)

        assert result.score == 50
        assert result.status == QualityStatus.WARN
        assert "Multiple critical evidence items are missing" in result.summary
        assert len(result.recommendations) >= 2


class TestInvestigationQualityEngine:
    def test_overall_score_averages_registered_metrics(self) -> None:
        registry = InvestigationQualityRegistry()

        @dataclass(frozen=True)
        class HighMetric(InvestigationQualityMetric):
            name: str = "high_metric"
            title: str = "High"

            def evaluate(self, case: Case) -> QualityMetricResult:
                return QualityMetricResult(
                    metric_name=self.name,
                    score=100,
                    max_score=100,
                    status=QualityStatus.PASS,
                    summary="High",
                    recommendations=(),
                )

        @dataclass(frozen=True)
        class LowMetric(InvestigationQualityMetric):
            name: str = "low_metric"
            title: str = "Low"

            def evaluate(self, case: Case) -> QualityMetricResult:
                return QualityMetricResult(
                    metric_name=self.name,
                    score=50,
                    max_score=100,
                    status=QualityStatus.WARN,
                    summary="Low",
                    recommendations=(),
                )

        registry.register_metric(HighMetric())
        registry.register_metric(LowMetric())

        report = InvestigationQualityEngine(registry=registry).evaluate_case(_case())

        assert report.overall_score == 75
        assert report.overall_status == QualityStatus.WARN
        assert report.ready_for_recommendation is True
        assert report.ready_for_case_closure is False

    def test_default_registry_includes_evidence_completeness(self) -> None:
        report = InvestigationQualityEngine().evaluate_case(_case())

        assert len(report.metric_results) == 1
        assert report.metric_results[0].metric_name == EVIDENCE_COMPLETENESS_METRIC_NAME


class TestInvestigationQualityRuntimeIntegration:
    def test_evaluate_investigation_quality_stores_report_on_case(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        try:
            report = runtime.evaluate_investigation_quality(case_id)
            case = runtime.case_manager.load_case(case_id)

            assert case.discovery_plan is not None
            assert case.investigation_quality_report is report
            assert report.overall_score == 75
            assert report.ready_for_recommendation is True
            assert report.ready_for_case_closure is False
        finally:
            runtime.shutdown()

    def test_evaluate_investigation_quality_raises_for_missing_case(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        with pytest.raises(CaseNotFoundError):
            runtime_engine.evaluate_investigation_quality("CASE-does-not-exist")

    def test_report_includes_investigation_quality_section(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        try:
            runtime.evaluate_investigation_quality(case_id)
            case = runtime.case_manager.load_case(case_id)
            case.status = InvestigationState.CLOSED

            report = build_incident_report(case)
            markdown = format_incident_report(report)

            assert report.investigation_quality.available is True
            assert report.investigation_quality.overall_score == 75
            assert "## Investigation Quality" in markdown
            assert "**Overall Score:** 75/100" in markdown
            assert "### Evidence Completeness" in markdown
            assert "debug ccsip messages" in markdown
        finally:
            runtime.shutdown()

    def test_report_without_quality_shows_placeholder(self) -> None:
        case = _case(status=InvestigationState.CLOSED)
        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert report.investigation_quality.available is False
        assert "_No investigation quality report recorded._" in markdown


class TestInvestigationQualityCli:
    def test_quality_scenario_prints_report(self) -> None:
        from cli.voicepilot_cli import run_quality_scenario

        output: list[str] = []
        code = run_quality_scenario(
            PLAYBOOK_ID,
            output.append,
            scenario_id="provider_503",
        )

        text = "\n".join(output)
        assert code == 0
        assert text.startswith("# Investigation Quality Report")
        assert "Overall Score" in text
        assert "Evidence Completeness" in text

    def test_main_quality_scenario_command(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["quality-scenario", PLAYBOOK_ID, "--scenario", "provider_503"])
        finally:
            builtins.print = original_print

        text = "\n".join(output)
        assert code == 0
        assert "# Investigation Quality Report" in text

    def test_scenario_markdown_can_include_investigation_quality(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        report_path = tmp_path / "scenario_results.md"
        code = run_scenario_assessment(
            PLAYBOOK_ID,
            lambda _line: None,
            scenario_id="provider_503",
            output_path=report_path,
            include_quality=True,
        )

        assert code == 0
        content = report_path.read_text(encoding="utf-8")
        assert "## Investigation Quality" in content
        assert "Overall Score" in content
        assert "Evidence Completeness" in content


class TestInvestigationQualityReporting:
    def test_format_investigation_quality_markdown_includes_recommendations(self) -> None:
        report = InvestigationQualityEngine().evaluate_case(_case())
        markdown = format_investigation_quality_markdown(report)

        assert "Ready for Recommendation" in markdown
        assert "Ready for Case Closure" in markdown
        assert "Recommendations" in markdown

    def test_format_report_section_lists_metric_details(self) -> None:
        metric = QualityMetricResult(
            metric_name="evidence_completeness",
            score=50,
            max_score=100,
            status=QualityStatus.WARN,
            summary="Multiple critical evidence items are missing.",
            recommendations=("Collect missing evidence: `debug ccsip messages`",),
        )
        report = InvestigationQualityReport(
            overall_score=50,
            overall_status=QualityStatus.WARN,
            metric_results=(metric,),
            ready_for_recommendation=False,
            ready_for_case_closure=False,
            generated_at=datetime.now(timezone.utc),
        )

        lines = format_investigation_quality_report_section(report)
        text = "\n".join(lines)

        assert "## Investigation Quality" in text
        assert "**Ready for Recommendation:** No" in text
        assert "### Evidence Completeness" in text
        assert "Collect missing evidence" in text
