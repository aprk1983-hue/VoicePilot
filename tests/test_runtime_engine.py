"""Tests for RuntimeEngine v1 intake execution loop."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.event_bus import EventBus
from runtime.exceptions import CaseNotFoundError, PlaybookIdNotFoundError, QuestionNotFoundError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"
INTAKE_QUESTION_IDS = [
    "Q-INT-001",
    "Q-INT-002",
    "Q-INT-003",
    "Q-INT-004",
    "Q-INT-005",
]


@pytest.fixture
def runtime_engine(event_bus: EventBus) -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
        event_bus=event_bus,
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
    yield engine
    registry.clear()
    catalog.clear()


class TestRuntimeEngine:
    def test_start_investigation_creates_case(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        assert turn.case_id
        assert len(runtime_engine.case_manager.list_cases()) == 1

        case = runtime_engine.case_manager.load_case(turn.case_id)
        assert case.playbook_id == PLAYBOOK_ID
        assert case.status == InvestigationState.INTAKE
        assert case.metadata.get("plugin_name") == "cisco"

    def test_start_investigation_returns_first_question(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        assert turn.state == InvestigationState.INTAKE
        assert turn.question_id == "Q-INT-001"
        assert turn.prompt
        assert turn.next_action_type == "ask_question"
        assert turn.required is True
        assert turn.context["playbook_id"] == PLAYBOOK_ID

    def test_submit_answer_returns_next_question(self, runtime_engine: RuntimeEngine) -> None:
        first = runtime_engine.start_investigation(PLAYBOOK_ID)

        second = runtime_engine.submit_answer(
            first.case_id,
            first.question_id,
            "yes",
        )

        assert second.case_id == first.case_id
        assert second.state == InvestigationState.INTAKE
        assert second.question_id == "Q-INT-002"
        assert second.next_action_type == "ask_question"

        case = runtime_engine.case_manager.load_case(first.case_id)
        assert len(case.timeline_events) == 1
        assert case.timeline_events[0].event_type == "question_answered"

    def test_completing_intake_moves_case_to_discovery(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        for index, question_id in enumerate(INTAKE_QUESTION_IDS):
            assert turn.question_id == question_id
            turn = runtime_engine.submit_answer(turn.case_id, question_id, f"answer-{index}")

        case = runtime_engine.case_manager.load_case(turn.case_id)
        assert case.status == InvestigationState.DISCOVERY
        assert turn.state == InvestigationState.DISCOVERY
        assert turn.question_id == "Q-INT-006"

    def test_unknown_playbook_id_raises_error(self, runtime_engine: RuntimeEngine) -> None:
        with pytest.raises(PlaybookIdNotFoundError):
            runtime_engine.start_investigation("VP-DOES-NOT-EXIST")

    def test_unknown_case_id_raises_error(self, runtime_engine: RuntimeEngine) -> None:
        with pytest.raises(CaseNotFoundError):
            runtime_engine.submit_answer("case-nonexistent", "Q-INT-001", "yes")

    def test_unknown_question_id_raises_error(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)

        with pytest.raises(QuestionNotFoundError):
            runtime_engine.submit_answer(turn.case_id, "Q-UNKNOWN", "yes")
