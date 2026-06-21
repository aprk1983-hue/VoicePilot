"""Tests for the Microsoft Teams Professional Pack engineering knowledge library."""

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
INCIDENT_IDS = tuple(f"VP-MS-TEAMS-{index:06d}" for index in range(1, 26))
TEAMS_ASSET_COUNT = 50


@pytest.fixture(autouse=True)
def _reset_library_cache() -> None:
    reset_default_engineering_knowledge_engine()
    yield
    reset_default_engineering_knowledge_engine()


@pytest.fixture
def library():
    return load_engineering_knowledge_library(default_knowledge_library_root())


def _teams_assets(library, asset_type: EngineeringAssetType | None = None):
    assets = library.asset_registry.list_assets()
    teams = [asset for asset in assets if asset.product == "Teams Phone"]
    if asset_type is None:
        return teams
    return [asset for asset in teams if asset.asset_type == asset_type]


class TestMicrosoftTeamsKnowledgeLibrary:
    def test_all_twenty_five_incident_assets_load(self, library) -> None:
        incidents = _teams_assets(library, EngineeringAssetType.INCIDENT)
        incident_ids = {asset.asset_id for asset in incidents}

        assert len(incidents) == 25
        assert incident_ids == set(INCIDENT_IDS)

    def test_asset_ids_are_unique(self, library) -> None:
        teams_ids = [asset.asset_id for asset in _teams_assets(library)]

        assert len(teams_ids) == len(set(teams_ids))

    def test_required_fields_validate(self, library) -> None:
        for asset in _teams_assets(library):
            assert asset.asset_id
            assert asset.title
            assert asset.summary
            assert asset.vendor == "Microsoft"
            assert asset.product == "Teams Phone"
            assert asset.references
            assert asset.version
            assert asset.confidence > 0

        for asset in _teams_assets(library, EngineeringAssetType.INCIDENT):
            assert asset.metadata.get("symptoms")
            assert asset.metadata.get("expected_findings")
            assert asset.metadata.get("expected_hypotheses")
            assert asset.metadata.get("recommended_actions")
            assert asset.metadata.get("rollback_steps")
            assert asset.metadata.get("verification_steps")
            assert asset.related_asset_ids

    def test_support_asset_counts(self, library) -> None:
        assert len(_teams_assets(library)) == TEAMS_ASSET_COUNT
        assert len(_teams_assets(library, EngineeringAssetType.VERIFICATION_GUIDE)) == 10
        assert len(_teams_assets(library, EngineeringAssetType.RUNBOOK)) == 10
        assert len(_teams_assets(library, EngineeringAssetType.REFERENCE)) == 5

    def test_factory_validation_passes(self, library) -> None:
        assets = tuple(_teams_assets(library))
        report = EngineeringAssetFactory().validate_assets(assets)

        assert report.valid
        assert not report.duplicate_ids
        assert not report.duplicate_titles

    def test_quality_scores_meet_professional_threshold(self, library) -> None:
        assets = tuple(_teams_assets(library))
        scores = EngineeringAssetFactory().score_quality(assets)

        assert scores
        for score in scores:
            assert score.score >= 95, f"{score.asset_id} scored {score.score}"

    def test_statistics_include_teams_assets(self, library) -> None:
        assets = tuple(_teams_assets(library))
        stats = EngineeringAssetFactory().asset_statistics(assets)

        assert stats.total_assets == TEAMS_ASSET_COUNT
        assert stats.average_quality >= 95
        assert ("Microsoft", TEAMS_ASSET_COUNT) in stats.vendor_counts

    def test_search_finds_teams_phone_incidents(self, library) -> None:
        results = search_assets(library, "Teams")
        ids = {asset.asset_id for asset in results if asset.product == "Teams Phone"}

        assert "VP-MS-TEAMS-000001" in ids
        assert len(ids) == TEAMS_ASSET_COUNT

    def test_search_finds_direct_routing_incident(self, library) -> None:
        results = search_assets(library, "Direct Routing")
        ids = {asset.asset_id for asset in results if asset.product == "Teams Phone"}

        assert "VP-MS-TEAMS-000007" in ids

    def test_related_runbooks_verification_and_references_are_linked(self, library) -> None:
        incident = library.asset_registry.get("VP-MS-TEAMS-000001")

        assert "VP-MS-TEAMS-RB-006" in incident.related_asset_ids
        assert "VP-MS-TEAMS-VG-001" in incident.related_asset_ids
        assert "VP-MS-TEAMS-REF-004" in incident.related_asset_ids

        relationships = library.relationship_registry.find_for_knowledge("VP-MS-TEAMS-000001")
        targets = {relationship.target_knowledge_id for relationship in relationships}
        assert "VP-MS-TEAMS-RB-006" in targets

    def test_registry_contains_teams_knowledge_entries(self, library) -> None:
        knowledge_ids = {
            entry.knowledge_id
            for entry in library.knowledge_registry.list_knowledge()
            if entry.knowledge_id.startswith("VP-MS-TEAMS-")
        }

        assert len(knowledge_ids) == TEAMS_ASSET_COUNT

    def test_ekf_matches_license_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "teams admin license export",
                "teams_phone_license_missing",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-MS-TEAMS-000001" in matched_ids

    def test_ekf_matches_direct_routing_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "direct routing gateway status",
                "direct_routing_sbc_unreachable",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-MS-TEAMS-000007" in matched_ids

    def test_ekf_matches_emergency_calling_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "emergency calling policy export",
                "emergency_calling_policy_missing",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-MS-TEAMS-000014" in matched_ids


class TestMicrosoftTeamsAssetsCli:
    def test_cli_search_show_and_stats(self, library) -> None:
        search_output: list[str] = []
        assert run_assets_search("Teams", search_output.append, library=library) == 0
        assert "VP-MS-TEAMS-000001" in "\n".join(search_output)

        search_output = []
        assert run_assets_search("Direct Routing", search_output.append, library=library) == 0
        assert "VP-MS-TEAMS-000007" in "\n".join(search_output)

        show_output: list[str] = []
        assert run_assets_show("VP-MS-TEAMS-000001", show_output.append, library=library) == 0
        assert "teams phone license missing" in "\n".join(show_output).lower()

        stats_output: list[str] = []
        assert run_assets_stats(stats_output.append, library=library) == 0
        stats_text = "\n".join(stats_output)
        assert "Total Assets:" in stats_text
        assert "Microsoft" in stats_text

    def test_cli_validate_and_quality(self, library) -> None:
        validate_output: list[str] = []
        assert run_assets_validate(validate_output.append, library=library) == 0

        quality_output: list[str] = []
        assert run_assets_quality(quality_output.append, library=library) == 0
        assert "Average Quality:" in "\n".join(quality_output)

    def test_main_assets_commands_include_teams(self) -> None:
        assert main(["assets", "search", "Teams"]) == 0
        assert main(["assets", "search", "Direct Routing"]) == 0
        assert main(["assets", "show", "VP-MS-TEAMS-000001"]) == 0
        assert main(["assets", "stats"]) == 0
        assert main(["assets", "validate"]) == 0
        assert main(["assets", "quality"]) == 0
