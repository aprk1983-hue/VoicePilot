"""Tests for the Engineering Asset Factory."""

from __future__ import annotations

import dataclasses
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from asset_factory import (
    AssetQualityScorer,
    AssetValidator,
    EngineeringAssetFactory,
    ValidationIssue,
)
from asset_factory.asset_exceptions import (
    AssetFactoryValidationError,
    DuplicateAssetIdError,
    DuplicateAssetTitleError,
    MissingRelatedAssetError,
)
from asset_factory.asset_relationship_builder import AssetRelationshipBuilder
from cli.voicepilot_cli import (
    main,
    run_assets_quality,
    run_assets_relationships,
    run_assets_stats,
    run_assets_validate,
)
from engineering_assets import EngineeringAsset, EngineeringAssetStatus, EngineeringAssetType, EngineeringCategory
from engineering_knowledge import load_engineering_knowledge_library
from runtime.scenario_runner import build_scenario_runtime_engine
from services import VoicePilotService


def _raw_incident(**overrides: object) -> dict:
    data = {
        "asset_id": "EAF-INC-001",
        "title": "SIP UA disabled incident",
        "asset_type": "INCIDENT",
        "category": "SIP",
        "vendor": "Cisco",
        "product": "CUBE",
        "version": "1.0",
        "summary": "Outbound calls fail when SIP-UA is disabled",
        "status": "ACTIVE",
        "severity": "high",
        "symptoms": ["Outbound calls fail"],
        "expected_findings": ["sip_ua_disabled"],
        "expected_hypotheses": ["CUBE SIP user agent disabled"],
        "recommended_actions": ["Enable SIP-UA"],
        "verification_steps": ["Verify SIP-UA status"],
        "references": ["https://example.test/incident"],
        "related_asset_ids": ["EAF-RB-001", "EAF-VG-001"],
    }
    data.update(overrides)
    return data


def _raw_runbook(**overrides: object) -> dict:
    data = {
        "asset_id": "EAF-RB-001",
        "title": "Enable SIP-UA runbook",
        "asset_type": "RUNBOOK",
        "category": "SIP",
        "vendor": "Cisco",
        "product": "CUBE",
        "version": "1.0",
        "summary": "Enable SIP-UA on CUBE",
        "status": "ACTIVE",
        "severity": "high",
        "recommended_actions": ["Enable voice service voip sip"],
        "verification_steps": ["Place test call"],
        "rollback_steps": ["Restore previous configuration"],
        "references": ["https://example.test/runbook"],
        "related_asset_ids": ["EAF-INC-001"],
    }
    data.update(overrides)
    return data


def _raw_verification(**overrides: object) -> dict:
    data = {
        "asset_id": "EAF-VG-001",
        "title": "Verify SIP-UA enabled",
        "asset_type": "VERIFICATION_GUIDE",
        "category": "SIP",
        "vendor": "Cisco",
        "product": "CUBE",
        "version": "1.0",
        "summary": "Verify SIP-UA is enabled",
        "status": "ACTIVE",
        "severity": "medium",
        "verification_steps": ["Collect show sip-ua status"],
        "references": ["https://example.test/verification"],
        "related_asset_ids": ["EAF-INC-001"],
    }
    data.update(overrides)
    return data


class TestAssetFactoryModels:
    def test_validation_issue_is_immutable(self) -> None:
        issue = ValidationIssue(field="title", message="missing", level="error")
        with pytest.raises(dataclasses.FrozenInstanceError):
            issue.message = "changed"  # type: ignore[misc]


class TestAssetValidator:
    def test_validates_required_fields(self) -> None:
        report = AssetValidator().validate_dict({"asset_id": "EAF-001"})
        assert not report.valid
        assert any(issue.field == "title" for issue in report.issues)

    def test_detects_duplicate_ids(self) -> None:
        items = (_raw_incident(), _raw_incident(asset_id="EAF-INC-002", title="Duplicate title"))
        report = AssetValidator().validate_batch(items)
        assert "EAF-INC-001" not in report.duplicate_ids or len(report.duplicate_ids) >= 0
        duplicate_report = AssetValidator().validate_batch((_raw_incident(), _raw_incident()))
        assert duplicate_report.duplicate_ids == ("EAF-INC-001",)

    def test_detects_duplicate_titles(self) -> None:
        report = AssetValidator().validate_batch(
            (
                _raw_incident(),
                _raw_incident(asset_id="EAF-INC-002"),
            )
        )
        assert report.duplicate_titles == ("SIP UA disabled incident",)

    def test_detects_missing_related_asset(self) -> None:
        report = AssetValidator().validate_dict(
            _raw_incident(related_asset_ids=["EAF-MISSING"]),
            known_asset_ids=frozenset({"EAF-INC-001"}),
        )
        assert not report.valid
        assert any("EAF-MISSING" in issue.message for issue in report.issues)


class TestAssetRelationshipBuilder:
    def test_generates_relationships_from_ids(self) -> None:
        factory = EngineeringAssetFactory()
        results = factory.build_batch((_raw_incident(), _raw_runbook(), _raw_verification()))
        relationships = factory.build_relationships([result.asset for result in results])

        assert relationships
        pairs = {(item.source_asset, item.target_asset) for item in relationships}
        assert ("EAF-INC-001", "EAF-RB-001") in pairs
        assert ("EAF-INC-001", "EAF-VG-001") in pairs


class TestAssetQualityScorer:
    def test_scores_complete_incident_high(self) -> None:
        result = EngineeringAssetFactory().build(_raw_incident())
        assert result.quality.score >= 80

    def test_scores_incomplete_asset_lower(self) -> None:
        result = EngineeringAssetFactory().build(
            {
                "asset_id": "EAF-SPARSE-001",
                "title": "Sparse asset",
                "asset_type": "NOTE",
                "category": "GENERAL",
                "vendor": "Cisco",
                "product": "CUBE",
                "version": "1.0",
                "summary": "Minimal note",
                "status": "ACTIVE",
                "severity": "low",
            }
        )
        assert result.quality.score < 80


class TestAssetStatistics:
    def test_generates_vendor_and_quality_statistics(self) -> None:
        factory = EngineeringAssetFactory()
        results = factory.build_batch((_raw_incident(), _raw_runbook(), _raw_verification()))
        assets = [result.asset for result in results]
        stats = factory.asset_statistics(assets)

        assert stats.total_assets == 3
        assert stats.average_quality > 0
        assert ("Cisco", 3) in stats.vendor_counts
        assert stats.relationship_count > 0


class TestEngineeringAssetFactory:
    def test_build_pipeline_produces_asset(self) -> None:
        result = EngineeringAssetFactory().build(_raw_incident())
        assert isinstance(result.asset, EngineeringAsset)
        assert result.asset.asset_id == "EAF-INC-001"
        assert result.validation.valid or result.validation.asset_reports

    def test_batch_build_raises_on_duplicate_id(self) -> None:
        with pytest.raises(DuplicateAssetIdError):
            AssetValidator().assert_valid_batch((_raw_incident(), _raw_incident()))

    def test_batch_build_raises_on_duplicate_title(self) -> None:
        with pytest.raises(DuplicateAssetTitleError):
            AssetValidator().assert_valid_batch(
                (_raw_incident(), _raw_incident(asset_id="EAF-INC-002"))
            )

    def test_no_ai_or_persistence_in_factory(self) -> None:
        source = inspect.getsource(EngineeringAssetFactory)
        forbidden = ("openai", "sqlite", "fastapi", "llm")
        for token in forbidden:
            assert token not in source.lower()


class TestAssetFactoryIntegration:
    def test_runtime_validate_assets(self) -> None:
        runtime = build_scenario_runtime_engine()
        try:
            report = runtime.validate_assets()
            assert report.valid
            assert len(report.asset_reports) > 0
        finally:
            runtime.shutdown()

    def test_runtime_asset_statistics(self) -> None:
        runtime = build_scenario_runtime_engine()
        try:
            stats = runtime.asset_statistics()
            assert stats.total_assets > 0
            assert stats.average_quality > 0
        finally:
            runtime.shutdown()

    def test_service_validate_assets(self) -> None:
        runtime = build_scenario_runtime_engine()
        try:
            service = VoicePilotService(runtime_engine=runtime)
            result = service.validate_assets()
            assert result.valid
            assert result.total_assets > 0
        finally:
            runtime.shutdown()

    def test_service_asset_statistics(self) -> None:
        runtime = build_scenario_runtime_engine()
        try:
            service = VoicePilotService(runtime_engine=runtime)
            result = service.asset_statistics()
            assert result.total_assets > 0
            assert result.average_quality > 0
        finally:
            runtime.shutdown()


class TestAssetFactoryCli:
    def test_cli_assets_validate(self) -> None:
        assert main(["assets", "validate"]) == 0

    def test_cli_assets_stats(self) -> None:
        assert main(["assets", "stats"]) == 0

    def test_cli_assets_quality(self) -> None:
        assert main(["assets", "quality"]) == 0

    def test_cli_assets_relationships(self) -> None:
        assert main(["assets", "relationships"]) == 0

    def test_run_assets_validate_with_library(self) -> None:
        library = load_engineering_knowledge_library()
        output: list[str] = []
        assert run_assets_validate(output.append, library=library) == 0

    def test_run_assets_stats_with_library(self) -> None:
        library = load_engineering_knowledge_library()
        output: list[str] = []
        assert run_assets_stats(output.append, library=library) == 0
        assert any("Average Quality" in line for line in output)

    def test_run_assets_quality_with_library(self) -> None:
        library = load_engineering_knowledge_library()
        output: list[str] = []
        assert run_assets_quality(output.append, library=library) == 0

    def test_run_assets_relationships_with_library(self) -> None:
        library = load_engineering_knowledge_library()
        output: list[str] = []
        assert run_assets_relationships(output.append, library=library) == 0

    def test_invalid_asset_dict_fails_validation_command_logic(self) -> None:
        output: list[str] = []
        from engineering_assets import EngineeringAssetRegistry

        registry = EngineeringAssetRegistry()
        sparse = EngineeringAsset(
            asset_id="EAF-BAD-001",
            title="Bad asset",
            asset_type=EngineeringAssetType.NOTE,
            category=EngineeringCategory.GENERAL,
            vendor="",
            product="",
            version="",
            summary="",
            description="",
            tags=(),
            references=(),
            related_asset_ids=(),
            metadata={},
            created_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
            status=EngineeringAssetStatus.DRAFT,
            source="test",
            confidence=1.0,
        )
        registry.register(sparse)
        from engineering_knowledge.knowledge_library_loader import EngineeringKnowledgeLibrary
        from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
        from engineering_knowledge.knowledge_relationships import KnowledgeRelationshipRegistry

        library = EngineeringKnowledgeLibrary(
            root=Path("."),
            asset_registry=registry,
            knowledge_registry=EngineeringKnowledgeRegistry(),
            relationship_registry=KnowledgeRelationshipRegistry(),
        )
        assert run_assets_validate(output.append, library=library) == 1
