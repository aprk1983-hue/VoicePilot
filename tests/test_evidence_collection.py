"""Tests for evidence collection flow."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import (
    get_next_evidence_request,
    initialize_evidence_collection,
    submit_evidence,
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
REQUIRED_COMMANDS = [
    "show dial-peer voice summary",
    "show sip-ua status",
    "show run | sec voice service voip",
    "debug ccsip messages",
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


def _complete_intake(runtime_engine: RuntimeEngine):
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    return runtime_engine.case_manager.load_case(turn.case_id)


class TestEvidenceCollection:
    def test_first_evidence_request_is_dial_peer_summary(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _complete_intake(runtime_engine)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)

        request = initialize_evidence_collection(case, runtime_engine.case_manager, playbook)

        assert request is not None
        assert request.command == "show dial-peer voice summary"
        assert request.sequence == 1
        assert request.total == 4

    def test_evidence_is_saved_on_case(self, runtime_engine: RuntimeEngine) -> None:
        case = _complete_intake(runtime_engine)
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

        assert len(case.evidence) == 1
        evidence = case.evidence[0]
        assert evidence.case_id == case.case_id
        assert evidence.source_type == "cli_paste"
        assert evidence.raw_text == "dial-peer 1 voip up"
        assert evidence.source.command == "show dial-peer voice summary"
        assert evidence.collected_at is not None

    def test_next_evidence_request_advances(self, runtime_engine: RuntimeEngine) -> None:
        case = _complete_intake(runtime_engine)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        case = runtime_engine.case_manager.load_case(case.case_id)

        submit_evidence(
            case,
            runtime_engine.case_manager,
            "show dial-peer voice summary",
            "output-1",
        )
        case = runtime_engine.case_manager.load_case(case.case_id)
        request = get_next_evidence_request(case)

        assert request is not None
        assert request.command == "show sip-ua status"
        assert request.sequence == 2

    def test_all_required_evidence_moves_state_to_analysis(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _complete_intake(runtime_engine)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        case = runtime_engine.case_manager.load_case(case.case_id)

        for command in REQUIRED_COMMANDS:
            case = runtime_engine.case_manager.load_case(case.case_id)
            submit_evidence(case, runtime_engine.case_manager, command, f"output for {command}")

        case = runtime_engine.case_manager.load_case(case.case_id)
        assert case.status == InvestigationState.ANALYSIS
        assert len(case.evidence) == 4
        assert get_next_evidence_request(case) is None
