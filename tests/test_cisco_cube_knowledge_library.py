"""Tests for the Cisco CUBE engineering knowledge library."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.voicepilot_cli import main, run_assets_search, run_assets_show, run_assets_stats
from engineering_assets import EngineeringAssetType
from engineering_knowledge import (
    default_knowledge_library_root,
    load_engineering_knowledge_library,
    reset_default_engineering_knowledge_engine,
    search_assets,
)
from engineering_knowledge.engineering_knowledge_bootstrap import default_engineering_knowledge_engine
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_ROOT = default_scenarios_root(VP_CUBE_0001_PLAYBOOK_ID, repo_root=REPO_ROOT)
INCIDENT_IDS = tuple(f"VP-CISCO-CUBE-{index:06d}" for index in range(1, 11))


@pytest.fixture(autouse=True)
def _reset_library_cache() -> None:
    reset_default_engineering_knowledge_engine()
    yield
    reset_default_engineering_knowledge_engine()


@pytest.fixture
def library():
    return load_engineering_knowledge_library(default_knowledge_library_root())


class TestCiscoCubeKnowledgeLibrary:
    def test_all_ten_incident_assets_load(self, library) -> None:
        incidents = [
            asset
            for asset in library.asset_registry.find_by_type(EngineeringAssetType.INCIDENT)
            if asset.product == "CUBE"
        ]
        incident_ids = {asset.asset_id for asset in incidents}

        assert len(incidents) == 10
        assert incident_ids == set(INCIDENT_IDS)

    def test_asset_ids_are_unique(self, library) -> None:
        assets = library.asset_registry.list_assets()
        asset_ids = [asset.asset_id for asset in assets]

        assert len(asset_ids) == len(set(asset_ids))

    def test_required_fields_validate(self, library) -> None:
        for asset in library.asset_registry.list_assets():
            if asset.product != "CUBE":
                continue
            assert asset.asset_id
            assert asset.title
            assert asset.summary
            assert asset.vendor == "Cisco"
            assert asset.product == "CUBE"

    def test_search_finds_sip_ua_incident(self, library) -> None:
        results = search_assets(library, "sip-ua")
        ids = {asset.asset_id for asset in results}

        assert "VP-CISCO-CUBE-000001" in ids

    def test_search_finds_provider_503_incident(self, library) -> None:
        results = search_assets(library, "503")
        ids = {asset.asset_id for asset in results}

        assert "VP-CISCO-CUBE-000003" in ids

    def test_related_runbooks_verification_and_references_are_linked(self, library) -> None:
        incident = library.asset_registry.get("VP-CISCO-CUBE-000001")

        assert "VP-CISCO-CUBE-RB-001" in incident.related_asset_ids
        assert "VP-CISCO-CUBE-VG-001" in incident.related_asset_ids
        assert "VP-CISCO-CUBE-REF-001" in incident.related_asset_ids

        relationships = library.relationship_registry.find_for_knowledge("VP-CISCO-CUBE-000001")
        targets = {relationship.target_knowledge_id for relationship in relationships}
        assert "VP-CISCO-CUBE-RB-001" in targets

    def test_ekf_matches_sip_ua_disabled_scenario(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        scenario_dir = SCENARIOS_ROOT / "sip_ua_disabled"
        runtime, case_id = run_scenario_to_correlation(scenario_dir)
        try:
            case = runtime.case_manager.load_case(case_id)
            report = engine.evaluate_case(case)
        finally:
            runtime.shutdown()

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-CISCO-CUBE-000001" in matched_ids

    def test_ekf_matches_provider_503_scenario(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(scenario_dir)
        try:
            case = runtime.case_manager.load_case(case_id)
            report = engine.evaluate_case(case)
        finally:
            runtime.shutdown()

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-CISCO-CUBE-000003" in matched_ids

    def test_library_contains_minimum_support_assets(self, library) -> None:
        assert len(library.asset_registry.find_by_type(EngineeringAssetType.VERIFICATION_GUIDE)) >= 5
        assert len(library.asset_registry.find_by_type(EngineeringAssetType.RUNBOOK)) >= 5
        assert len(library.asset_registry.find_by_type(EngineeringAssetType.REFERENCE)) >= 5


class TestAssetsCli:
    def test_cli_search_show_and_stats(self, library) -> None:
        search_output: list[str] = []
        assert run_assets_search("sip-ua", search_output.append, library=library) == 0
        assert "VP-CISCO-CUBE-000001" in "\n".join(search_output)

        show_output: list[str] = []
        assert run_assets_show("VP-CISCO-CUBE-000001", show_output.append, library=library) == 0
        assert "CUBE SIP-UA disabled" in "\n".join(show_output)

        stats_output: list[str] = []
        assert run_assets_stats(stats_output.append, library=library) == 0
        assert "Total Assets:" in "\n".join(stats_output)
        assert "INCIDENT: 60" in "\n".join(stats_output)

    def test_main_assets_commands(self) -> None:
        assert main(["assets", "search", "sip-ua"]) == 0
        assert main(["assets", "show", "VP-CISCO-CUBE-000001"]) == 0
        assert main(["assets", "stats"]) == 0

    def test_show_missing_asset_returns_error(self, library) -> None:
        output: list[str] = []
        code = run_assets_show("VP-CISCO-CUBE-MISSING", output.append, library=library)
        assert code == 1
        assert "Asset not found" in "\n".join(output)
