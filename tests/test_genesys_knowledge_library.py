"""Tests for the Genesys Cloud CX Professional Pack engineering knowledge library."""

from __future__ import annotations

from pathlib import Path

import pytest

from asset_factory import EngineeringAssetFactory
from cli.voicepilot_cli import (
    main,
    run_assets_quality,
    run_assets_search,
    run_assets_show,
    run_assets_stats,
    run_assets_validate,
)
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
INCIDENT_IDS = tuple(f"VP-GENESYS-CLOUD-{index:06d}" for index in range(1, 26))
GENESYS_ASSET_COUNT = 50


@pytest.fixture(autouse=True)
def _reset_library_cache() -> None:
    reset_default_engineering_knowledge_engine()
    yield
    reset_default_engineering_knowledge_engine()


@pytest.fixture
def library():
    return load_engineering_knowledge_library(default_knowledge_library_root())


def _genesys_assets(library, asset_type: EngineeringAssetType | None = None):
    assets = library.asset_registry.list_assets()
    genesys = [asset for asset in assets if asset.vendor == "Genesys" and asset.product == "Cloud"]
    if asset_type is None:
        return genesys
    return [asset for asset in genesys if asset.asset_type == asset_type]


class TestGenesysKnowledgeLibrary:
    def test_all_twenty_five_incident_assets_load(self, library) -> None:
        incidents = _genesys_assets(library, EngineeringAssetType.INCIDENT)
        incident_ids = {asset.asset_id for asset in incidents}

        assert len(incidents) == 25
        assert incident_ids == set(INCIDENT_IDS)

    def test_asset_ids_are_unique(self, library) -> None:
        genesys_ids = [asset.asset_id for asset in _genesys_assets(library)]

        assert len(genesys_ids) == len(set(genesys_ids))

    def test_required_fields_validate(self, library) -> None:
        for asset in _genesys_assets(library):
            assert asset.asset_id
            assert asset.title
            assert asset.summary
            assert asset.vendor == "Genesys"
            assert asset.product == "Cloud"
            assert asset.references
            assert asset.version
            assert asset.confidence > 0

        for asset in _genesys_assets(library, EngineeringAssetType.INCIDENT):
            assert asset.metadata.get("symptoms")
            assert asset.metadata.get("expected_findings")
            assert asset.metadata.get("expected_hypotheses")
            assert asset.metadata.get("recommended_actions")
            assert asset.metadata.get("rollback_steps")
            assert asset.metadata.get("verification_steps")
            assert asset.related_asset_ids

    def test_support_asset_counts(self, library) -> None:
        assert len(_genesys_assets(library)) == GENESYS_ASSET_COUNT
        assert len(_genesys_assets(library, EngineeringAssetType.VERIFICATION_GUIDE)) == 10
        assert len(_genesys_assets(library, EngineeringAssetType.RUNBOOK)) == 10
        assert len(_genesys_assets(library, EngineeringAssetType.REFERENCE)) == 5

    def test_factory_validation_passes(self, library) -> None:
        assets = tuple(_genesys_assets(library))
        report = EngineeringAssetFactory().validate_assets(assets)

        assert report.valid
        assert not report.duplicate_ids
        assert not report.duplicate_titles

    def test_quality_scores_meet_professional_threshold(self, library) -> None:
        assets = tuple(_genesys_assets(library))
        scores = EngineeringAssetFactory().score_quality(assets)

        assert scores
        for score in scores:
            assert score.score >= 100, f"{score.asset_id} scored {score.score}"

    def test_statistics_include_genesys_assets(self, library) -> None:
        assets = tuple(_genesys_assets(library))
        stats = EngineeringAssetFactory().asset_statistics(assets)

        assert stats.total_assets == GENESYS_ASSET_COUNT
        assert stats.average_quality >= 100
        assert ("Genesys", GENESYS_ASSET_COUNT) in stats.vendor_counts

    def test_search_finds_genesys_cloud_incidents(self, library) -> None:
        results = search_assets(library, "Genesys")
        ids = {asset.asset_id for asset in results if asset.product == "Cloud"}

        assert "VP-GENESYS-CLOUD-000001" in ids
        assert len(ids) == GENESYS_ASSET_COUNT

    def test_search_finds_oauth_failure_incident(self, library) -> None:
        results = search_assets(library, "OAuth failure")
        ids = {asset.asset_id for asset in results if asset.product == "Cloud"}

        assert "VP-GENESYS-CLOUD-000002" in ids

    def test_search_finds_byoc_cloud_trunk_incident(self, library) -> None:
        results = search_assets(library, "BYOC Cloud trunk")
        ids = {asset.asset_id for asset in results if asset.product == "Cloud"}

        assert "VP-GENESYS-CLOUD-000024" in ids

    def test_related_runbooks_verification_and_references_are_linked(self, library) -> None:
        incident = library.asset_registry.get("VP-GENESYS-CLOUD-000001")

        assert "VP-GENESYS-CLOUD-RB-001" in incident.related_asset_ids
        assert "VP-GENESYS-CLOUD-VG-001" in incident.related_asset_ids
        assert "VP-GENESYS-CLOUD-REF-002" in incident.related_asset_ids

        relationships = library.relationship_registry.find_for_knowledge("VP-GENESYS-CLOUD-000001")
        targets = {relationship.target_knowledge_id for relationship in relationships}
        assert "VP-GENESYS-CLOUD-RB-001" in targets

    def test_registry_contains_genesys_knowledge_entries(self, library) -> None:
        knowledge_ids = {
            entry.knowledge_id
            for entry in library.knowledge_registry.list_knowledge()
            if entry.knowledge_id.startswith("VP-GENESYS-CLOUD-")
        }

        assert len(knowledge_ids) == GENESYS_ASSET_COUNT

    def test_ekf_matches_oauth_failure_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "oauth client export",
                "oauth_failure",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-GENESYS-CLOUD-000002" in matched_ids

    def test_ekf_matches_sip_options_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "trunk status export",
                "sip_options_failure",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-GENESYS-CLOUD-000008" in matched_ids

    def test_ekf_matches_queue_unavailable_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "queue configuration export",
                "queue_unavailable",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-GENESYS-CLOUD-000010" in matched_ids

    def test_all_incident_categories_represented(self, library) -> None:
        incidents = _genesys_assets(library, EngineeringAssetType.INCIDENT)
        titles = {asset.title.lower() for asset in incidents}

        expected_phrases = (
            "authentication",
            "oauth",
            "token expired",
            "organization unavailable",
            "edge offline",
            "trunk unavailable",
            "carrier unavailable",
            "sip options",
            "tls certificate",
            "queue unavailable",
            "queue member",
            "agent not logged",
            "agent stuck",
            "call flow",
            "architect publish",
            "data action",
            "recording failure",
            "conversation service",
            "analytics unavailable",
            "webrtc",
            "media service",
            "outbound campaign",
            "presence synchronization",
            "byoc cloud",
            "byoc premises",
        )
        for phrase in expected_phrases:
            assert any(phrase in title for title in titles), f"missing category phrase: {phrase}"

    def test_runbook_and_reference_ids_follow_pack_convention(self, library) -> None:
        runbooks = _genesys_assets(library, EngineeringAssetType.RUNBOOK)
        references = _genesys_assets(library, EngineeringAssetType.REFERENCE)

        assert {asset.asset_id for asset in runbooks} == {
            f"VP-GENESYS-CLOUD-RB-{index:03d}" for index in range(1, 11)
        }
        assert {asset.asset_id for asset in references} == {
            f"VP-GENESYS-CLOUD-REF-{index:03d}" for index in range(1, 6)
        }


class TestGenesysAssetsCli:
    def test_cli_search_show_and_stats(self, library) -> None:
        search_output: list[str] = []
        assert run_assets_search("Genesys", search_output.append, library=library) == 0
        assert "VP-GENESYS-CLOUD-000001" in "\n".join(search_output)

        search_output = []
        assert run_assets_search("OAuth failure", search_output.append, library=library) == 0
        assert "VP-GENESYS-CLOUD-000002" in "\n".join(search_output)

        show_output: list[str] = []
        assert run_assets_show("VP-GENESYS-CLOUD-000001", show_output.append, library=library) == 0
        assert "authentication failure" in "\n".join(show_output).lower()

        stats_output: list[str] = []
        assert run_assets_stats(stats_output.append, library=library) == 0
        stats_text = "\n".join(stats_output)
        assert "Total Assets:" in stats_text
        assert "Genesys" in stats_text

    def test_cli_validate_and_quality(self, library) -> None:
        validate_output: list[str] = []
        assert run_assets_validate(validate_output.append, library=library) == 0

        quality_output: list[str] = []
        assert run_assets_quality(quality_output.append, library=library) == 0
        assert "Average Quality:" in "\n".join(quality_output)

    def test_main_assets_commands_include_genesys(self) -> None:
        assert main(["assets", "search", "Genesys"]) == 0
        assert main(["assets", "search", "OAuth failure"]) == 0
        assert main(["assets", "show", "VP-GENESYS-CLOUD-000001"]) == 0
        assert main(["assets", "stats"]) == 0
        assert main(["assets", "validate"]) == 0
        assert main(["assets", "quality"]) == 0
