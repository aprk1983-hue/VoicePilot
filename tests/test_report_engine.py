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
from runtime.report_engine import ReportEngine, build_incident_report, format_incident_report
from runtime.runtime_engine import RuntimeEngine
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
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
        "dial-peer 1 voip up",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        "SIP-UA Status: disabled",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        "SIP/2.0 503 Service Unavailable",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    runtime_engine.analyze_case(case.case_id)
    runtime_engine.generate_hypotheses(case.case_id)
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
        assert report.confidence == 90.0
        assert any(finding.signal == "sip_ua_disabled" for finding in report.findings)
        assert report.recommendation_summary
        assert report.verification_outcome == "all_steps_passed"
        assert report.verifications
        assert report.learning_record_id == case.learning_record.learning_record_id
        assert report.learning_root_cause == "CUBE SIP user agent disabled"
        assert report.learning_reusable_pattern.startswith("VP-CUBE-0001:")

        assert "CUBE SIP user agent disabled" in markdown
        assert "90%" in markdown
        assert "sip_ua_disabled" in markdown
        assert "Verification" in markdown
        assert "Learning Record" in markdown

    def test_report_engine_builds_report_directly(self, runtime_engine: RuntimeEngine) -> None:
        case = _closed_case(runtime_engine)
        report = ReportEngine().generate(case)

        assert report.symptom
        assert report.findings

    def test_cannot_generate_report_if_not_closed(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        with pytest.raises(InvalidInvestigationStateError):
            runtime_engine.generate_report(turn.case_id)
