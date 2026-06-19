"""Tests for verification engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case, Hypothesis, Recommendation
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE, ACTION_NEXT_BEST
from runtime.verification_engine import (
    OUTCOME_COMPLETE,
    OUTCOME_FAILED,
    RESULT_FAILED,
    RESULT_PASSED,
    VerificationEngine,
    VerificationResultSubmission,
)
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


def _case_in_resolution(runtime_engine: RuntimeEngine) -> Case:
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
        "show run | sec voice service voip",
        "voice service voip\n no sip\n",
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
    runtime_engine.correlate_case(case.case_id)
    runtime_engine.generate_recommendation(case.case_id)
    return runtime_engine.case_manager.load_case(case.case_id)


def _case_in_investigation_with_next_best(runtime_engine: RuntimeEngine) -> Case:
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
        "SIP User Agent Status: enabled",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show run | sec voice service voip",
        "voice service voip\n sip\n",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        "From: a\nTo: b\nCall-ID: c\nSIP/2.0 503 Service Unavailable",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    runtime_engine.analyze_case(case.case_id)
    runtime_engine.generate_hypotheses(case.case_id)
    runtime_engine.generate_recommendation(case.case_id)
    return runtime_engine.case_manager.load_case(case.case_id)


class TestVerificationEngine:
    def test_checklist_created_for_likely_root_cause(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_resolution(runtime_engine)

        checklist = runtime_engine.generate_verification_checklist(case.case_id)

        assert checklist is not None
        assert checklist.likely_root_cause == "CUBE SIP user agent disabled"
        assert len(checklist.items) == 3

    def test_no_checklist_for_next_best_action(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_investigation_with_next_best(runtime_engine)

        checklist = runtime_engine.generate_verification_checklist(case.case_id)

        assert checklist is None
        assert case.recommendations[-1].action_type == ACTION_NEXT_BEST

    def test_all_passed_transitions_to_learning(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_resolution(runtime_engine)
        checklist = runtime_engine.generate_verification_checklist(case.case_id)
        assert checklist is not None

        submissions = [
            VerificationResultSubmission(
                verification_id=item.verification_id,
                status=RESULT_PASSED,
            )
            for item in checklist.items
        ]

        summary = runtime_engine.submit_verification(case.case_id, submissions)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert summary.outcome == OUTCOME_COMPLETE
        assert updated.status == InvestigationState.LEARNING

    def test_failed_transitions_back_to_investigation(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_resolution(runtime_engine)
        checklist = runtime_engine.generate_verification_checklist(case.case_id)
        assert checklist is not None

        submissions = [
            VerificationResultSubmission(
                verification_id=checklist.items[0].verification_id,
                status=RESULT_FAILED,
                notes="SIP-UA still disabled",
            )
        ]

        summary = runtime_engine.submit_verification(case.case_id, submissions)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert summary.outcome == OUTCOME_FAILED
        assert updated.status == InvestigationState.INVESTIGATION
        assert "Root cause not verified" in updated.metadata.get("verification_note", "")

    def test_verification_results_saved_on_case(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_resolution(runtime_engine)
        checklist = runtime_engine.generate_verification_checklist(case.case_id)
        assert checklist is not None

        runtime_engine.submit_verification(
            case.case_id,
            [
                VerificationResultSubmission(
                    verification_id=checklist.items[0].verification_id,
                    status=RESULT_PASSED,
                    notes="enabled",
                )
            ],
        )
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert len(updated.verifications) == 3
        assert updated.verifications[0].result_status == RESULT_PASSED
        assert updated.verifications[0].notes == "enabled"
