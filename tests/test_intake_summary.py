"""Tests for intake summary builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.intake_summary import (
    CHANGE_ROUTING_STRATEGY,
    VP_CUBE_0001_ALL_FAIL_EVIDENCE,
    build_intake_summary,
    format_intake_summary,
)
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"


@pytest.fixture
def vp_cube_playbook() -> object:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
    )
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    return catalog.get(PLAYBOOK_ID)


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


def _case_with_metadata(metadata: dict) -> Case:
    case = Case.create(
        title="Outbound PSTN failure",
        symptom=SymptomSummary(summary="outbound calls fail"),
        severity=Severity.HIGH,
        business_impact="Users cannot call externally",
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco", products=("cube",)),
        playbook_id=PLAYBOOK_ID,
        metadata=metadata,
    )
    case.status = InvestigationState.DISCOVERY
    return case


def _complete_intake(runtime_engine: RuntimeEngine, answers: list[str]) -> Case:
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in answers:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    return runtime_engine.case_manager.load_case(turn.case_id)


class TestBuildIntakeSummary:
    def test_summary_includes_case_and_playbook_fields(self, runtime_engine: RuntimeEngine) -> None:
        case = _complete_intake(
            runtime_engine,
            ["yes", "2026-06-10", "no changes", "all destinations", "yes"],
        )
        summary = build_intake_summary(case)

        assert summary.case_id == case.case_id
        assert summary.playbook_id == PLAYBOOK_ID
        assert summary.current_state == InvestigationState.DISCOVERY

    def test_summary_includes_known_facts_from_intake(self, runtime_engine: RuntimeEngine) -> None:
        case = _complete_intake(
            runtime_engine,
            ["yes", "2026-06-10", "firewall change", "all destinations", "yes"],
        )
        summary = build_intake_summary(case)

        assert summary.known_facts["worked_previously"] == "yes"
        assert summary.known_facts["recent_changes"] == "firewall change"
        assert summary.known_facts["onset"] == "2026-06-10"
        assert summary.known_facts["destination_classes"] == "all destinations"
        assert summary.known_facts["inbound_working"] == "yes"

    def test_change_and_routing_strategy_when_worked_before_and_recent_change(self) -> None:
        case = _case_with_metadata(
            {
                "known_facts": {"worked_previously": "yes", "inbound_working": "yes"},
                "recent_changes": "Updated dial-peer on CUBE",
                "affected_scope": {"destination_classes": "mobile only"},
            }
        )
        summary = build_intake_summary(case)

        assert summary.recommended_strategy == CHANGE_ROUTING_STRATEGY

    def test_all_outbound_fail_includes_missing_evidence_commands(self) -> None:
        case = _case_with_metadata(
            {
                "known_facts": {"worked_previously": "no"},
                "recent_changes": "none",
                "affected_scope": {"destination_classes": "all outbound calls fail"},
            }
        )
        summary = build_intake_summary(case)

        assert summary.missing_evidence == VP_CUBE_0001_ALL_FAIL_EVIDENCE
        assert summary.next_required_commands == VP_CUBE_0001_ALL_FAIL_EVIDENCE

    def test_format_intake_summary_renders_sections(self, runtime_engine: RuntimeEngine) -> None:
        case = _complete_intake(
            runtime_engine,
            ["yes", "2026-06-10", "no changes", "all destinations", "yes"],
        )
        rendered = format_intake_summary(build_intake_summary(case))

        assert "--- Intake Summary ---" in rendered
        assert "Known Facts:" in rendered
        assert "Missing Evidence:" in rendered
        assert "Recommended Strategy:" in rendered
        assert "Next Required Commands:" in rendered
        assert "show dial-peer voice summary" in rendered
