"""Tests for the AudioCodes SBC Professional Pack engineering knowledge library."""

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
INCIDENT_IDS = tuple(f"VP-AUDIOCODES-SBC-{index:06d}" for index in range(1, 26))
SBC_ASSET_COUNT = 50


@pytest.fixture(autouse=True)
def _reset_library_cache() -> None:
    reset_default_engineering_knowledge_engine()
    yield
    reset_default_engineering_knowledge_engine()


@pytest.fixture
def library():
    return load_engineering_knowledge_library(default_knowledge_library_root())


def _sbc_assets(library, asset_type: EngineeringAssetType | None = None):
    assets = library.asset_registry.list_assets()
    sbc = [asset for asset in assets if asset.product == "SBC"]
    if asset_type is None:
        return sbc
    return [asset for asset in sbc if asset.asset_type == asset_type]


class TestAudioCodesKnowledgeLibrary:
    def test_all_twenty_five_incident_assets_load(self, library) -> None:
        incidents = _sbc_assets(library, EngineeringAssetType.INCIDENT)
        incident_ids = {asset.asset_id for asset in incidents}

        assert len(incidents) == 25
        assert incident_ids == set(INCIDENT_IDS)

    def test_asset_ids_are_unique(self, library) -> None:
        sbc_ids = [asset.asset_id for asset in _sbc_assets(library)]

        assert len(sbc_ids) == len(set(sbc_ids))

    def test_required_fields_validate(self, library) -> None:
        for asset in _sbc_assets(library):
            assert asset.asset_id
            assert asset.title
            assert asset.summary
            assert asset.vendor == "AudioCodes"
            assert asset.product == "SBC"
            assert asset.references
            assert asset.version
            assert asset.confidence > 0

        for asset in _sbc_assets(library, EngineeringAssetType.INCIDENT):
            assert asset.metadata.get("symptoms")
            assert asset.metadata.get("expected_findings")
            assert asset.metadata.get("expected_hypotheses")
            assert asset.metadata.get("recommended_actions")
            assert asset.metadata.get("rollback_steps")
            assert asset.metadata.get("verification_steps")
            assert asset.related_asset_ids

    def test_support_asset_counts(self, library) -> None:
        assert len(_sbc_assets(library)) == SBC_ASSET_COUNT
        assert len(_sbc_assets(library, EngineeringAssetType.VERIFICATION_GUIDE)) == 10
        assert len(_sbc_assets(library, EngineeringAssetType.RUNBOOK)) == 10
        assert len(_sbc_assets(library, EngineeringAssetType.REFERENCE)) == 5

    def test_factory_validation_passes(self, library) -> None:
        assets = tuple(_sbc_assets(library))
        report = EngineeringAssetFactory().validate_assets(assets)

        assert report.valid
        assert not report.duplicate_ids
        assert not report.duplicate_titles

    def test_quality_scores_meet_professional_threshold(self, library) -> None:
        assets = tuple(_sbc_assets(library))
        scores = EngineeringAssetFactory().score_quality(assets)

        assert scores
        for score in scores:
            assert score.score >= 100, f"{score.asset_id} scored {score.score}"

    def test_statistics_include_sbc_assets(self, library) -> None:
        assets = tuple(_sbc_assets(library))
        stats = EngineeringAssetFactory().asset_statistics(assets)

        assert stats.total_assets == SBC_ASSET_COUNT
        assert stats.average_quality >= 100
        assert ("AudioCodes", SBC_ASSET_COUNT) in stats.vendor_counts

    def test_search_finds_audiocodes_sbc_incidents(self, library) -> None:
        results = search_assets(library, "AudioCodes")
        ids = {asset.asset_id for asset in results if asset.product == "SBC"}

        assert "VP-AUDIOCODES-SBC-000001" in ids
        assert len(ids) == SBC_ASSET_COUNT

    def test_search_finds_tls_certificate_incident(self, library) -> None:
        results = search_assets(library, "TLS certificate")
        ids = {asset.asset_id for asset in results if asset.product == "SBC"}

        assert "VP-AUDIOCODES-SBC-000003" in ids

    def test_search_finds_ha_failover_incident(self, library) -> None:
        results = search_assets(library, "HA failover")
        ids = {asset.asset_id for asset in results if asset.product == "SBC"}

        assert "VP-AUDIOCODES-SBC-000015" in ids

    def test_related_runbooks_verification_and_references_are_linked(self, library) -> None:
        incident = library.asset_registry.get("VP-AUDIOCODES-SBC-000001")

        assert "VP-AUDIOCODES-SBC-RB-001" in incident.related_asset_ids
        assert "VP-AUDIOCODES-SBC-VG-001" in incident.related_asset_ids
        assert "VP-AUDIOCODES-SBC-REF-002" in incident.related_asset_ids

        relationships = library.relationship_registry.find_for_knowledge("VP-AUDIOCODES-SBC-000001")
        targets = {relationship.target_knowledge_id for relationship in relationships}
        assert "VP-AUDIOCODES-SBC-RB-001" in targets

    def test_registry_contains_sbc_knowledge_entries(self, library) -> None:
        knowledge_ids = {
            entry.knowledge_id
            for entry in library.knowledge_registry.list_knowledge()
            if entry.knowledge_id.startswith("VP-AUDIOCODES-SBC-")
        }

        assert len(knowledge_ids) == SBC_ASSET_COUNT

    def test_ekf_matches_sip_options_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "sip interface status export",
                "sip_options_failure",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-AUDIOCODES-SBC-000001" in matched_ids

    def test_ekf_matches_tls_certificate_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "tls certificate export",
                "tls_certificate_expired",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-AUDIOCODES-SBC-000003" in matched_ids

    def test_ekf_matches_registration_failure_finding(self, library) -> None:
        engine = default_engineering_knowledge_engine()
        findings = (
            AnalysisFinding.create(
                "CASE-1",
                "EVD-1",
                "registration status export",
                "registration_failure",
            ),
        )
        report = engine.evaluate_findings(findings)

        matched_ids = {match.knowledge_id for match in report.matches}
        assert "VP-AUDIOCODES-SBC-000025" in matched_ids

    def test_all_incident_categories_represented(self, library) -> None:
        incidents = _sbc_assets(library, EngineeringAssetType.INCIDENT)
        titles = {asset.title.lower() for asset in incidents}

        expected_phrases = (
            "sip options",
            "provider 503",
            "tls certificate",
            "tls negotiation",
            "sip interface",
            "proxy set",
            "ip group",
            "routing table",
            "manipulation set",
            "media realm",
            "rtp one-way",
            "srtp",
            "session license",
            "ha failover",
            "standby synchronization",
            "sip flood",
            "dos protection",
            "488",
            "403",
            "408",
            "sbc overload",
            "dns resolution",
            "gateway unreachable",
            "registration failure",
        )
        for phrase in expected_phrases:
            assert any(phrase in title for title in titles), f"missing category phrase: {phrase}"

    def test_runbook_and_reference_ids_follow_pack_convention(self, library) -> None:
        runbooks = _sbc_assets(library, EngineeringAssetType.RUNBOOK)
        references = _sbc_assets(library, EngineeringAssetType.REFERENCE)

        assert {asset.asset_id for asset in runbooks} == {
            f"VP-AUDIOCODES-SBC-RB-{index:03d}" for index in range(1, 11)
        }
        assert {asset.asset_id for asset in references} == {
            f"VP-AUDIOCODES-SBC-REF-{index:03d}" for index in range(1, 6)
        }


class TestAudioCodesAssetsCli:
    def test_cli_search_show_and_stats(self, library) -> None:
        search_output: list[str] = []
        assert run_assets_search("AudioCodes", search_output.append, library=library) == 0
        assert "VP-AUDIOCODES-SBC-000001" in "\n".join(search_output)

        search_output = []
        assert run_assets_search("TLS certificate", search_output.append, library=library) == 0
        assert "VP-AUDIOCODES-SBC-000003" in "\n".join(search_output)

        show_output: list[str] = []
        assert run_assets_show("VP-AUDIOCODES-SBC-000001", show_output.append, library=library) == 0
        assert "sip options failure" in "\n".join(show_output).lower()

        stats_output: list[str] = []
        assert run_assets_stats(stats_output.append, library=library) == 0
        stats_text = "\n".join(stats_output)
        assert "Total Assets:" in stats_text
        assert "AudioCodes" in stats_text

    def test_cli_validate_and_quality(self, library) -> None:
        validate_output: list[str] = []
        assert run_assets_validate(validate_output.append, library=library) == 0

        quality_output: list[str] = []
        assert run_assets_quality(quality_output.append, library=library) == 0
        assert "Average Quality:" in "\n".join(quality_output)

    def test_main_assets_commands_include_audiocodes(self) -> None:
        assert main(["assets", "search", "AudioCodes"]) == 0
        assert main(["assets", "search", "TLS certificate"]) == 0
        assert main(["assets", "show", "VP-AUDIOCODES-SBC-000001"]) == 0
        assert main(["assets", "stats"]) == 0
        assert main(["assets", "validate"]) == 0
        assert main(["assets", "quality"]) == 0
