"""Tests for VoicePilot CLI v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.voicepilot_cli import read_multiline_paste, run_investigation
from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
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
EVIDENCE_INPUTS = [
    "dial-peer 1 voip up",
    "END",
    "SIP UAS registered",
    "END",
    "SIP/2.0 404 Not Found",
    "END",
]
FULL_INPUTS = INTAKE_ANSWERS + EVIDENCE_INPUTS


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


class TestReadMultilinePaste:
    def test_cli_supports_end_marker(self) -> None:
        inputs = iter(["line one", "line two", "END", "ignored"])
        pasted = read_multiline_paste(lambda: next(inputs))

        assert pasted == "line one\nline two"


class TestRunInvestigation:
    def test_cli_can_start_investigation(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        answers = iter(FULL_INPUTS)

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
        answers = iter(FULL_INPUTS)

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
        answers = iter(FULL_INPUTS)

        run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert any("[Q-INT-002]" in line for line in output)
        assert any("[Q-INT-005]" in line for line in output)

    def test_cli_reaches_discovery_and_collects_evidence(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        output: list[str] = []
        answers = iter(FULL_INPUTS)

        code = run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        assert code == 0
        assert "Intake complete. Next phase: DISCOVERY." in output
        assert "--- Intake Summary ---" in "\n".join(output)
        assert any("Please provide command output:" in line for line in output)
        assert any(line == "show dial-peer voice summary" for line in output)
        assert "Evidence collection complete. Next phase: ANALYSIS." in output
        assert "Analysis complete. Next phase: HYPOTHESIS." in output
        assert any(line == "Findings:" for line in output)
        assert any("sip_404_detected" in line for line in output)

        case_id = next(line.split(":", 1)[1].strip() for line in output if line.startswith("Case:"))
        case = runtime_engine.case_manager.load_case(case_id)
        assert case.status == InvestigationState.HYPOTHESIS
        assert len(case.evidence) == 3
        assert any(finding.signal == "sip_404_detected" for finding in case.analysis_findings)

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
