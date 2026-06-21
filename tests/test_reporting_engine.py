"""Tests for the Enterprise Reporting Engine."""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from cli.voicepilot_cli import main, run_report_case, run_report_scenario
from domain.enums import Severity
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from domain.models import Case
from reporting import EnterpriseReportEngine, READ_ONLY_NOTICE, ReportType
from reporting.report_engine import EnterpriseReportEngine as EREClass
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from runtime.report_engine import ReportEngine, build_incident_report, format_incident_report
from services import VoicePilotService
from services.service_models import ReportResult

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

FORBIDDEN_TERMS_CUSTOMER = ("show sip-ua", "debug ccsip", "dial-peer", "CUBE")


@pytest.fixture
def sip_ua_case():
    scenario_dir = SCENARIOS_ROOT / "sip_ua_disabled"
    runtime, case_id = run_scenario_to_correlation(scenario_dir)
    runtime.generate_recommendation(case_id)
    try:
        yield runtime, case_id
    finally:
        runtime.shutdown()


class TestReportingModels:
    def test_models_are_immutable(self) -> None:
        engine = EnterpriseReportEngine()
        case = Case.create(
            title="Test",
            symptom=SymptomSummary(summary="Outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="Users cannot call externally",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        report = engine.generate(case, ReportType.EXECUTIVE)
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.title = "changed"  # type: ignore[misc]


class TestEnterpriseReportEngine:
    def test_engineering_report_reuses_existing_report_engine(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        incident = build_incident_report(case)
        expected_markdown = format_incident_report(incident)

        report = EnterpriseReportEngine().generate(case, ReportType.ENGINEERING)

        assert report.report_type == ReportType.ENGINEERING
        assert incident.top_hypothesis_title in report.markdown
        assert "VoicePilot Incident Report" in report.markdown
        for section in ("## Case Overview", "## Evidence Findings"):
            assert section in expected_markdown
            assert section in report.markdown

    def test_executive_report_generation(self, sip_ua_case) -> None:
        _, case_id = sip_ua_case
        runtime, _ = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        report = EnterpriseReportEngine().generate(case, ReportType.EXECUTIVE)

        assert report.report_type == ReportType.EXECUTIVE
        assert "# Executive Incident Report" in report.markdown
        assert "## Business Impact" in report.markdown
        assert report.business_impact

    def test_customer_report_generation(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        report = EnterpriseReportEngine().generate(case, ReportType.CUSTOMER)

        assert report.report_type == ReportType.CUSTOMER
        assert "# Customer Incident Summary" in report.markdown
        lowered = report.markdown.lower()
        for term in FORBIDDEN_TERMS_CUSTOMER:
            assert term.lower() not in lowered

    def test_cab_report_generation(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        report = EnterpriseReportEngine().generate(case, ReportType.CAB)

        assert report.report_type == ReportType.CAB
        assert "# Change Advisory Report" in report.markdown
        assert "## Rollback" in report.markdown
        assert "## Verification" in report.markdown
        assert "## Approvals" in report.markdown

    def test_operations_report_generation(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        report = EnterpriseReportEngine().generate(case, ReportType.OPERATIONS)

        assert report.report_type == ReportType.OPERATIONS
        assert "# Operations Report" in report.markdown
        assert "## Investigation Quality" in report.markdown
        assert "## Open Findings" in report.markdown

    def test_read_only_notice_always_present(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        for report_type in ReportType:
            report = EnterpriseReportEngine().generate(case, report_type)
            assert READ_ONLY_NOTICE in report.markdown
            assert "## Read-Only Notice" in report.markdown

    def test_no_duplicate_diagnosis_logic(self) -> None:
        source = inspect.getsource(EREClass)
        forbidden = (
            "HypothesisEngine(",
            "RecommendationEngine(",
            "AnalysisEngine(",
            "CorrelationEngine(",
        )
        for token in forbidden:
            assert token not in source


class TestReportingIntegration:
    def test_runtime_generate_report_with_type(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        report = runtime.generate_report(case_id, ReportType.EXECUTIVE)

        assert report.report_id.startswith("RPT-")
        assert report.report_type == ReportType.EXECUTIVE

    def test_service_generate_report_returns_dto(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        service = VoicePilotService(runtime_engine=runtime)
        result = service.generate_report(case_id, ReportType.EXECUTIVE)

        assert isinstance(result, ReportResult)
        assert result.case_id == case_id
        assert result.report_id
        assert result.report_type == "EXECUTIVE"
        assert "# Executive Incident Report" in result.markdown


class TestReportingCli:
    def test_cli_report_scenario_executive(self, tmp_path: Path) -> None:
        output_path = tmp_path / "executive_report.md"
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "sip_ua_disabled",
                    "--type",
                    "executive",
                    "--output",
                    str(output_path),
                ]
            )
            == 0
        )
        content = output_path.read_text(encoding="utf-8")
        assert READ_ONLY_NOTICE in content
        assert "# Executive Incident Report" in content

    @pytest.mark.parametrize(
        "report_type",
        ["engineering", "executive", "customer", "cab", "operations"],
    )
    def test_cli_report_scenario_all_types(self, report_type: str) -> None:
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "sip_ua_disabled",
                    "--type",
                    report_type,
                ]
            )
            == 0
        )

    def test_run_report_scenario_writes_output_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "report.md"
        output: list[str] = []
        code = run_report_scenario(
            PLAYBOOK_ID,
            output.append,
            scenario_id="sip_ua_disabled",
            report_type=ReportType.OPERATIONS,
            output_path=output_path,
            repo_root=REPO_ROOT,
        )
        assert code == 0
        assert output_path.exists()
        assert "# Operations Report" in output_path.read_text(encoding="utf-8")

    def test_run_report_case_not_found(self) -> None:
        output: list[str] = []
        code = run_report_case("CASE-does-not-exist", output.append)
        assert code == 1
        assert "Case not found" in "\n".join(output)

    def test_existing_runtime_report_engine_still_used_for_legacy_path(self) -> None:
        assert ReportEngine is not None
        assert callable(build_incident_report)
        assert callable(format_incident_report)
