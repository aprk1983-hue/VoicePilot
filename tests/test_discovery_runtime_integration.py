"""Tests for discovery planner runtime integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from discovery.planner_models import DiscoveryPlan
from domain.enums import DecisionLogEntryType, InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.exceptions import CaseNotFoundError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.report_engine import build_incident_report, format_incident_report
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import (
    EVIDENCE_FILES,
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=PLUGINS_ROOT.parent)
PARTIAL_EVIDENCE_FILES = EVIDENCE_FILES[:2]


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
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


class TestDiscoveryRuntimeIntegration:
    def test_plan_discovery_stores_plan_on_case(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        try:
            plan = runtime.plan_discovery(case_id)
            case = runtime.case_manager.load_case(case_id)

            assert isinstance(plan, DiscoveryPlan)
            assert case.discovery_plan is plan
            assert plan.next_best_command is not None
            assert any(
                entry.decision_type == DecisionLogEntryType.DISCOVERY_PLANNED
                for entry in case.decision_log
            )
        finally:
            runtime.shutdown()

    def test_partial_evidence_recommends_missing_commands(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        try:
            plan = runtime.plan_discovery(case_id)
            commands = {request.command for request in plan.requests}

            assert "debug ccsip messages" in commands
            assert "show run | sec voice service voip" in commands
            assert plan.next_best_command == "show run | sec voice service voip"
        finally:
            runtime.shutdown()

    def test_plan_discovery_raises_for_missing_case(self, runtime_engine: RuntimeEngine) -> None:
        with pytest.raises(CaseNotFoundError):
            runtime_engine.plan_discovery("CASE-does-not-exist")

    def test_report_includes_discovery_plan_section(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        try:
            runtime.plan_discovery(case_id)
            case = runtime.case_manager.load_case(case_id)
            case.status = InvestigationState.CLOSED

            report = build_incident_report(case)
            markdown = format_incident_report(report)

            assert report.discovery_plan.available is True
            assert report.discovery_plan.next_best_command == "show run | sec voice service voip"
            assert "## Discovery Plan" in markdown
            assert "**Next Best Command:** `show run | sec voice service voip`" in markdown
            assert "debug ccsip messages" in markdown
        finally:
            runtime.shutdown()

    def test_report_without_discovery_plan_shows_placeholder(self) -> None:
        from domain.enums import Severity
        from domain.models import Case
        from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary

        case = Case(
            case_id="CASE-NO-PLAN",
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

        assert report.discovery_plan.available is False
        assert "## Discovery Plan" in markdown
        assert "_No discovery plan recorded._" in markdown
