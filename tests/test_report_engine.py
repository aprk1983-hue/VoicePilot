"""Tests for report engine and incident report generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.exceptions import InvalidInvestigationStateError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.report_engine import (
    ReportEngine,
    build_incident_report,
    format_incident_report,
)
from runtime.runtime_engine import RuntimeEngine
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PARSER_SAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "sample_evidence" / "parser"
PLAYBOOK_ID = "VP-CUBE-0001"
INTAKE_ANSWERS = [
    "yes",
    "2026-06-10",
    "no changes",
    "all destinations",
    "yes",
]


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
    )
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


def _closed_case(runtime_engine: RuntimeEngine):
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    case = runtime_engine.case_manager.load_case(turn.case_id)
    playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
    initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
    case = runtime_engine.case_manager.load_case(case.case_id)

    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show dial-peer voice summary",
        (PARSER_SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8"),
        decision_log=runtime_engine.decision_log_engine,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        "SIP-UA Status: disabled",
        decision_log=runtime_engine.decision_log_engine,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show run | sec voice service voip",
        "voice service voip\n no sip\n",
        decision_log=runtime_engine.decision_log_engine,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        "SIP/2.0 503 Service Unavailable",
        decision_log=runtime_engine.decision_log_engine,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    runtime_engine.analyze_case(case.case_id)
    runtime_engine.generate_hypotheses(case.case_id)
    runtime_engine.correlate_case(case.case_id)
    runtime_engine.generate_recommendation(case.case_id)
    case = runtime_engine.case_manager.load_case(case.case_id)

    checklist = runtime_engine.generate_verification_checklist(case.case_id)
    assert checklist is not None
    submissions = [
        VerificationResultSubmission(
            verification_id=item.verification_id,
            status=RESULT_PASSED,
        )
        for item in checklist.items
    ]
    runtime_engine.submit_verification(case.case_id, submissions)
    runtime_engine.close_case_with_learning(case.case_id)
    return runtime_engine.case_manager.load_case(case.case_id)


class TestReportEngine:
    def test_report_generated_for_closed_case(self, runtime_engine: RuntimeEngine) -> None:
        case = _closed_case(runtime_engine)

        report = runtime_engine.generate_report(case.case_id)

        assert report.case_id == case.case_id
        assert report.playbook_id == PLAYBOOK_ID
        assert report.final_state == InvestigationState.CLOSED

    def test_report_includes_root_cause_confidence_evidence_verification_learning(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _closed_case(runtime_engine)
        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert report.top_hypothesis_title == "CUBE SIP user agent disabled"
        assert report.confidence == 98.0
        assert any(finding.signal == "sip_ua_disabled" for finding in report.findings)
        assert report.recommendation_summary
        assert report.verification_outcome == "all_steps_passed"
        assert report.verifications
        assert report.learning_record_id == case.learning_record.learning_record_id
        assert report.learning_root_cause == "CUBE SIP user agent disabled"
        assert report.learning_reusable_pattern.startswith("VP-CUBE-0001:")

        assert "CUBE SIP user agent disabled" in markdown
        assert "98%" in markdown
        assert "sip_ua_disabled" in markdown
        assert "parser:cisco_show_sip_ua_status" in markdown
        assert "sip_ua_enabled=False" in markdown
        assert "Verification" in markdown
        assert "Learning Record" in markdown
        assert "## Correlation Reasoning" in markdown
        assert any(
            correlation.rule_id == "sip_ua_disabled_confirmed" for correlation in report.correlations
        )
        assert "sip_ua_disabled_confirmed" in markdown
        assert "+8 confidence" in markdown
        assert "Evidence: sip_ua_disabled, sip_ua_disabled_by_config" in markdown
        assert "## Decision Timeline" in markdown
        assert "CiscoShowSipUaStatusParser" in markdown
        assert "sip_ua_disabled_confirmed" in markdown
        assert any(decision.title == "sip_ua_disabled_confirmed" for decision in report.decisions)
        assert "## Canonical Voice Objects" in markdown
        assert "SipUA — SIP-UA — cisco_show_sip_ua_status" in markdown
        assert "VoiceService — voice service voip — cisco_show_run_voice_service_voip" in markdown
        assert "DialPeer 1 — destination 9T — cisco_show_dial_peer_voice_summary" in markdown
        assert len(report.voice_objects) == 4
        assert "## Call Path Analysis" in markdown
        assert "### DialPeer 1 → Provider-192.0.2.10" in markdown
        assert "**Direction:** outbound" in markdown
        assert "1. DialPeer 1" in markdown
        assert "SIP-UA is disabled and may affect all SIP call processing" in markdown
        assert report.call_path_analysis.disabled_sip_ua_note is not None
        assert len(report.call_path_analysis.paths) >= 1

    def test_report_without_correlations_still_works(self) -> None:
        from domain.enums import InvestigationState, Severity
        from domain.models import Case
        from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary

        case = Case(
            case_id="CASE-NO-CORR",
            title="test",
            status=InvestigationState.CLOSED,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="outbound calls fail"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
            playbook_id=PLAYBOOK_ID,
        )

        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert report.correlations == ()
        assert report.decisions == ()
        assert "## Correlation Reasoning" in markdown
        assert "## Decision Timeline" in markdown
        assert "_No correlation results recorded._" in markdown
        assert "_No decision log entries recorded._" in markdown
        assert "_No canonical voice objects recorded._" in markdown
        assert "_No call paths derived from current evidence._" in markdown
        assert report.call_path_analysis.paths == ()
        assert "# VoicePilot Incident Report" in markdown

    def test_call_path_analysis_handles_no_paths_gracefully(self) -> None:
        from domain.enums import InvestigationState, Severity
        from domain.models import Case
        from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
        from model import SipUA

        def _provenance(**overrides: str) -> dict[str, str]:
            base = {
                "vendor": "cisco",
                "platform": "CUBE",
                "hostname": "cube-edge-01",
                "source_parser": "cisco_show_sip_ua_status",
                "source_command": "show sip-ua status",
                "source_evidence_id": "EVD-test-001",
            }
            base.update(overrides)
            return base

        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        case = Case(
            case_id="CASE-CALL-PATH",
            title="test",
            status=InvestigationState.CLOSED,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="outbound calls fail"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
            playbook_id=PLAYBOOK_ID,
            voice_objects=[sip_ua],
        )

        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert "_No call paths derived from current evidence._" in markdown
        assert "SIP-UA is disabled and may affect all SIP call processing" in markdown
        assert report.call_path_analysis.disabled_sip_ua_note is not None

    def test_report_engine_builds_report_directly(self, runtime_engine: RuntimeEngine) -> None:
        case = _closed_case(runtime_engine)
        report = ReportEngine().generate(case)

        assert report.symptom
        assert report.findings

    def test_cannot_generate_report_if_not_closed(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        with pytest.raises(InvalidInvestigationStateError):
            runtime_engine.generate_report(turn.case_id)
