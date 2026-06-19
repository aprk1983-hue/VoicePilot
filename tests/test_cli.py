"""Tests for VoicePilot CLI v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.voicepilot_cli import run_investigation
from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
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
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
    )
    engine.start()
    return engine


class TestRunInvestigation:
    def test_cli_can_start_investigation(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        answers = iter(INTAKE_ANSWERS)

        code = run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert code == 0
        assert output[0] == "Investigation started"
        assert any(line.startswith("Case:") for line in output)

    def test_cli_prints_first_question(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        answers = iter(INTAKE_ANSWERS)

        run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert any("[Q-INT-001]" in line for line in output)
        assert any("Did outbound PSTN calling ever work" in line for line in output)

    def test_cli_accepts_answers_through_fake_input_provider(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        output: list[str] = []
        answers = iter(INTAKE_ANSWERS)

        run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert any("[Q-INT-002]" in line for line in output)
        assert any("[Q-INT-005]" in line for line in output)

    def test_cli_reaches_discovery(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        answers = iter(INTAKE_ANSWERS)

        code = run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert code == 0
        assert "Intake complete. Next phase: DISCOVERY." in output

        case_id = next(line.split(":", 1)[1].strip() for line in output if line.startswith("Case:"))
        case = runtime_engine.case_manager.load_case(case_id)
        assert case.status == InvestigationState.DISCOVERY

    def test_unknown_playbook_returns_non_zero(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []

        code = run_investigation(
            "VP-DOES-NOT-EXIST",
            input_provider=lambda: "",
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert code != 0
        assert any("Playbook not found" in line for line in output)
