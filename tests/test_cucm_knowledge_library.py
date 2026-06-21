"""Tests for the Cisco CUCM engineering knowledge library."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.voicepilot_cli import main, run_assets_search, run_assets_show, run_assets_stats
from domain.models import AnalysisFinding
from engineering_assets import EngineeringAssetType
from engineering_knowledge import (
    default_knowledge_library_root,
    load_engineering_knowledge_library,
    reset_default_engineering_knowledge_engine,
    search_assets,
)
from engineering_knowledge.engineering_knowledge_bootstrap import default_engineering_knowledge_engine

REPO_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_IDS = tuple(f"VP-CISCO-CUCM-{index:06d}" for index in range(1, 26))


@pytest.fixture(autouse=True)
def _reset_library_cache() -> None:
    reset_default_engineering_knowledge_engine()
    yield
    reset_default_engineering_knowledge_engine()


@pytest.fixture
def library():
    return load_engineering_knowledge_library(default_knowledge_library_root())


def _cucm_assets(library, asset_type: EngineeringAssetType | None = None):
    assets = library.asset_registry.list_assets()
    cucm = [asset for asset in assets if asset.product == "CUCM"]
    if asset_type is None:
        return cucm
    return [asset for asset in cucm if asset.asset_type == asset_type]


class TestCiscoCucmKnowledgeLibrary:
    def test_all_twenty_five_incident_assets_load(self, library) -> None:
        incidents = _cucm_assets(library, EngineeringAssetType.INCIDENT)
        incident_ids = {asset.asset_id for asset in incidents}

        assert len(incidents) == 25
        assert incident_ids == set(INCIDENT_IDS)

    def test_asset_ids_are_unique(self, library) -> None:
        cucm_ids = [asset.asset_id for asset in _cucm_assets(library)]

        assert len(cucm_ids) == len(set(cucm_ids))

    def test_required_fields_validate(self, library) -> None:
        for asset in _cucm_assets(library):
            assert asset.asset_id
            assert asset.title
            assert asset.summary
            assert asset.vendor == "Cisco"
            assert asset.product == "CUCM"
            assert asset.references
            assert asset.version
            assert asset.confidence > 0

        for asset in _cucm_assets(library, EngineeringAssetType.INCIDENT):
            assert asset.metadata.get("symptoms")
            assert asset.metadata.get("required_evidence")
            assert asset.metadata.get("expected_findings")
            assert asset.metadata.get("recommended_actions")
            assert asset.metadata.get("verification_steps")

    def test_support_asset_counts(self, library) -> None:
        assert len(_cucm_assets(library, EngineeringAssetType.VERIFICATION_GUIDE)) == 10
        assert len(_cucm_assets(library, EngineeringAssetType.RUNBOOK)) == 10
        assert len(_cucm_assets(library, EngineeringAssetType.REFERENCE)) == 10

    def test_search_finds_phone_registration_incident(self, library) -> None:
        results = search_assets(library, "tftp")
        ids = {asset.asset_id for asset in results if asset.product == "CUCM"}

        assert "VP-CISCO-CUCM-000001" in ids

    def test_search_finds_sip_trunk_incident(self, library) -> None:
        results = search_assets(library, "sip trunk")
        ids = {asset.asset_id for asset in results if asset.product == "CUCM"}

        assert "VP-CISCO-CUCM-000006" in ids

    def test_related_runbooks_verification_and_references_are_linked(self, library) -> None:
        incident = library.asset_registry.get("VP-CISCO-CUCM-000001")

        assert "VP-CISCO-CUCM-RB-001" in incident.related_asset_ids
        assert "VP-CISCO-CUCM-VG-001" in incident.related_asset_ids
        assert "VP-CISCO-CUCM-REF-001" in incident.related_asset_ids

        relationships = library.relationship_registry.find_for_knowledge("VP-CISCO-CUCM-000001")
        targets = {relationship.target_knowledge_id for relationship in relationships}
        assert "VP-CISCO-CUCM-RB-001" in targets

    def test_registry_contains_cucm_knowledge_entries(self, library) -> None:
        knowledge_ids = {
            entry.knowledge_id
            for entry in library.knowledge_registry.list_knowledge()
            if entry.knowledge_id.startswith("VP-CISCO-CUCM-")
        }

        assert len(knowledge_ids) == 55

    def test_ekf_matches_phone_registration_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create("CASE-1", "EVD-1", "phone syslog", "phone_tftp_unreachable"),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-CISCO-CUCM-000001" in matched_ids

    def test_ekf_matches_sip_trunk_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create("CASE-1", "EVD-1", "sip trunk status", "sip_trunk_down"),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-CISCO-CUCM-000006" in matched_ids

    def test_ekf_matches_cluster_replication_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create("CASE-1", "EVD-1", "dbreplication", "db_replication_broken"),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-CISCO-CUCM-000021" in matched_ids


class TestCucmAssetsCli:
    def test_cli_search_show_and_stats(self, library) -> None:
        search_output: list[str] = []
        assert run_assets_search("tftp", search_output.append, library=library) == 0
        assert "VP-CISCO-CUCM-000001" in "\n".join(search_output)

        show_output: list[str] = []
        assert run_assets_show("VP-CISCO-CUCM-000001", show_output.append, library=library) == 0
        assert "TFTP unreachable" in "\n".join(show_output)

        stats_output: list[str] = []
        assert run_assets_stats(stats_output.append, library=library) == 0
        stats_text = "\n".join(stats_output)
        assert "Total Assets:" in stats_text
        assert "INCIDENT: 35" in stats_text

    def test_main_assets_commands_include_cucm(self) -> None:
        assert main(["assets", "search", "sip trunk"]) == 0
        assert main(["assets", "show", "VP-CISCO-CUCM-000006"]) == 0
        assert main(["assets", "stats"]) == 0
