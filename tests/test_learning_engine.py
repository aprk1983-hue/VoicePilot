"""Tests for learning engine and case closure."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.exceptions import InvalidInvestigationStateError
from runtime.learning_engine import LearningEngine
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission
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


def _case_in_learning(runtime_engine: RuntimeEngine):
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
    return runtime_engine.case_manager.load_case(case.case_id)


class TestLearningEngine:
    def test_learning_record_created_from_verified_case(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_learning(runtime_engine)

        closure = runtime_engine.close_case_with_learning(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert updated.learning_record is not None
        assert closure.learning_record_id == updated.learning_record.learning_record_id

    def test_case_transitions_to_closed(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_learning(runtime_engine)

        closure = runtime_engine.close_case_with_learning(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert closure.state == InvestigationState.CLOSED
        assert updated.status == InvestigationState.CLOSED
        assert updated.closed_at is not None

    def test_learning_record_includes_root_cause_confidence_and_evidence(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_learning(runtime_engine)

        runtime_engine.close_case_with_learning(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)
        record = updated.learning_record
        assert record is not None

        assert record.root_cause == "CUBE SIP user agent disabled"
        assert record.confidence == 98.0
        assert record.playbook_id == PLAYBOOK_ID
        assert "sip_ua_disabled" in record.evidence_summary
        assert record.evidence_finding_ids
        assert record.verification_summary
        assert record.lessons_learned
        assert record.reusable_pattern.startswith("VP-CUBE-0001:")

    def test_cannot_close_case_if_not_in_learning(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        with pytest.raises(InvalidInvestigationStateError):
            runtime_engine.close_case_with_learning(turn.case_id)

    def test_learning_engine_builds_record_directly(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_learning(runtime_engine)
        record = LearningEngine().create_learning_record(case)

        assert record.symptom
        assert record.final_outcome == "verified_and_closed"
        assert record.hypothesis_id
