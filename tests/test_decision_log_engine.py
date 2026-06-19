"""Tests for append-only decision log engine."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from domain.enums import DecisionLogEntryType, InvestigationState, Severity
from domain.models import AnalysisFinding, Case, Hypothesis
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.decision_log_engine import (
    DecisionLogEngine,
    DecisionLogImmutableError,
    format_decision_timeline,
    parser_display_name,
)
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.hypothesis_engine import VP_CUBE_0001_PLAYBOOK_ID
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
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


def _empty_case(case_id: str = "CASE-DLOG") -> Case:
    return Case(
        case_id=case_id,
        title="test",
        status=InvestigationState.ANALYSIS,
        severity=Severity.HIGH,
        business_impact="test",
        symptom=SymptomSummary(summary="outbound calls fail"),
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco"),
        playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
    )


def _closed_case(runtime_engine: RuntimeEngine) -> Case:
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    case = runtime_engine.case_manager.load_case(turn.case_id)
    playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
    initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
    case = runtime_engine.case_manager.load_case(case.case_id)
    decision_log = runtime_engine.decision_log_engine

    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show dial-peer voice summary",
        "dial-peer 1 voip up",
        decision_log=decision_log,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        "SIP-UA Status: disabled",
        decision_log=decision_log,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show run | sec voice service voip",
        "voice service voip\n no sip\n",
        decision_log=decision_log,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        "SIP/2.0 503 Service Unavailable",
        decision_log=decision_log,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    runtime_engine.analyze_case(case.case_id)
    runtime_engine.generate_hypotheses(case.case_id)
    runtime_engine.correlate_case(case.case_id)
    runtime_engine.generate_recommendation(case.case_id)
    case = runtime_engine.case_manager.load_case(case.case_id)

    checklist = runtime_engine.generate_verification_checklist(case.case_id)
    assert checklist is not None
    from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission

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


class TestDecisionLogEngineUnit:
    def test_parser_display_name(self) -> None:
        assert parser_display_name("cisco_show_sip_ua_status") == "CiscoShowSipUaStatusParser"

    def test_append_parser_decision(self) -> None:
        case = _empty_case()
        engine = DecisionLogEngine()

        entry = engine.append_parser_decision(
            case,
            parser_name="CiscoShowSipUaStatusParser",
            parser_id="cisco_show_sip_ua_status",
            signal="sip_ua_disabled",
            evidence_id="EVD-1",
            command="show sip-ua status",
            finding_id="FIND-1",
        )

        assert len(case.decision_log) == 1
        assert entry.decision_type == DecisionLogEntryType.PARSER_RESULT
        assert entry.title == "CiscoShowSipUaStatusParser"
        assert "sip_ua_disabled" in entry.description
        assert entry.rule_name == "cisco_show_sip_ua_status"
        assert entry.supporting_evidence == ("EVD-1",)

    def test_append_analysis_decision(self) -> None:
        case = _empty_case()
        finding = AnalysisFinding.create(
            case.case_id,
            "EVD-2",
            "debug ccsip messages",
            "sip_503_detected",
        )
        entry = DecisionLogEngine().append_analysis_decision(case, finding=finding)

        assert entry.decision_type == DecisionLogEntryType.ANALYSIS_RESULT
        assert entry.supporting_findings == (finding.finding_id,)

    def test_append_correlation_and_confidence_change(self) -> None:
        case = _empty_case()
        hypothesis = Hypothesis.create(
            case_id=case.case_id,
            title="CUBE SIP user agent disabled",
            confidence=90.0,
            supporting_finding_ids=[],
            rank=1,
        )
        case.hypotheses = [hypothesis]
        from domain.models import CorrelationResult

        correlation = CorrelationResult.create(
            case.case_id,
            "reinforcement",
            "sip_ua_disabled_confirmed",
            "Operational status and running configuration both indicate SIP-UA is disabled.",
            finding_codes=["sip_ua_disabled", "sip_ua_disabled_by_config"],
            confidence_delta=8.0,
            hypothesis_id=hypothesis.hypothesis_id,
        )
        engine = DecisionLogEngine()
        engine.append_correlation_decision(
            case,
            correlation=correlation,
            confidence_before=90.0,
            confidence_after=98.0,
        )
        hypothesis.confidence = 98.0
        engine.append_confidence_change(
            case,
            hypothesis=hypothesis,
            confidence_before=90.0,
            confidence_after=98.0,
            trigger="reinforcement",
            rule_name="sip_ua_disabled_confirmed",
            correlation_id=correlation.correlation_id,
        )

        types = [entry.decision_type for entry in case.decision_log]
        assert DecisionLogEntryType.CORRELATION in types
        assert DecisionLogEntryType.CONFIDENCE_INCREASED in types

    def test_decision_log_is_append_only(self) -> None:
        case = _empty_case()
        engine = DecisionLogEngine()
        entry = engine.append_parser_decision(
            case,
            parser_name="CiscoShowSipUaStatusParser",
            parser_id="cisco_show_sip_ua_status",
            signal="sip_ua_disabled",
            evidence_id="EVD-1",
            command="show sip-ua status",
        )
        original = case.decision_log[0]

        with pytest.raises(DecisionLogImmutableError):
            engine.append(case, replace(entry, entry_id=entry.entry_id))

        assert case.decision_log[0] is original
        assert len(case.decision_log) == 1


class TestDecisionLogRuntimeIntegration:
    def test_full_investigation_appends_expected_decisions(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _closed_case(runtime_engine)
        types = {entry.decision_type for entry in case.decision_log}

        assert DecisionLogEntryType.EVIDENCE_COLLECTED in types
        assert DecisionLogEntryType.PARSER_RESULT in types
        assert DecisionLogEntryType.HYPOTHESIS_CREATED in types
        assert DecisionLogEntryType.CORRELATION in types
        assert DecisionLogEntryType.CONFIDENCE_INCREASED in types
        assert DecisionLogEntryType.RECOMMENDATION_SELECTED in types
        assert DecisionLogEntryType.VERIFICATION_COMPLETED in types
        assert DecisionLogEntryType.LEARNING_CREATED in types
        assert DecisionLogEntryType.CASE_CLOSED in types

    def test_timeline_order_is_chronological(self, runtime_engine: RuntimeEngine) -> None:
        case = _closed_case(runtime_engine)
        timestamps = [entry.timestamp for entry in case.decision_log]
        assert timestamps == sorted(timestamps)

    def test_timeline_includes_parser_correlation_and_recommendation(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _closed_case(runtime_engine)
        rendered = format_decision_timeline(case.decision_log)

        assert "CiscoShowSipUaStatusParser" in rendered
        assert "sip_ua_disabled_confirmed" in rendered
        assert "Likely Root Cause" in rendered
        assert "↓" in rendered

    def test_recommendation_logs_selected_hypothesis(self, runtime_engine: RuntimeEngine) -> None:
        case = _closed_case(runtime_engine)
        recommendation_entries = [
            entry
            for entry in case.decision_log
            if entry.decision_type == DecisionLogEntryType.RECOMMENDATION_SELECTED
        ]

        assert recommendation_entries
        assert recommendation_entries[0].selected_hypothesis is not None
        assert recommendation_entries[0].confidence_after is not None
