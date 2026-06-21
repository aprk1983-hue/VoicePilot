"""Tests for the Engineering Asset Framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from engineering_assets import (
    DuplicateEngineeringAssetError,
    DuplicateEngineeringRelationshipError,
    EngineeringAsset,
    EngineeringAssetLoader,
    EngineeringAssetNotFoundError,
    EngineeringAssetRegistry,
    EngineeringAssetReport,
    EngineeringAssetSearch,
    EngineeringAssetStatus,
    EngineeringAssetType,
    EngineeringAssetValidationError,
    EngineeringCategory,
    EngineeringRelationship,
    EngineeringRelationshipRegistry,
    EngineeringRelationshipType,
)


def _asset(
    asset_id: str,
    *,
    vendor: str = "ExampleVendor",
    product: str = "ExampleProduct",
    asset_type: EngineeringAssetType = EngineeringAssetType.RUNBOOK,
    category: EngineeringCategory = EngineeringCategory.VOICE,
    tags: tuple[str, ...] = ("sip", "verification"),
) -> EngineeringAsset:
    now = datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc)
    return EngineeringAsset(
        asset_id=asset_id,
        title=f"Asset {asset_id}",
        asset_type=asset_type,
        category=category,
        vendor=vendor,
        product=product,
        version="1.0",
        summary=f"Summary for {asset_id}",
        description=f"Description for {asset_id}",
        tags=tags,
        references=("https://example.test/reference",),
        related_asset_ids=(),
        metadata={"owner": "platform"},
        created_at=now,
        updated_at=now,
        status=EngineeringAssetStatus.ACTIVE,
        source="unit-test",
        confidence=0.95,
    )


class TestEngineeringAssetModels:
    def test_engineering_asset_is_immutable(self) -> None:
        asset = _asset("EAF-001")

        with pytest.raises(FrozenInstanceError):
            asset.title = "changed"  # type: ignore[misc]

    def test_engineering_relationship_is_immutable(self) -> None:
        relationship = EngineeringRelationship(
            source_asset="EAF-001",
            target_asset="EAF-002",
            relationship_type=EngineeringRelationshipType.REFERENCES,
        )

        with pytest.raises(FrozenInstanceError):
            relationship.target_asset = "EAF-003"  # type: ignore[misc]


class TestEngineeringAssetRegistry:
    def test_register_get_list_and_remove(self) -> None:
        registry = EngineeringAssetRegistry()
        first = _asset("EAF-001")
        second = _asset("EAF-002", vendor="OtherVendor")

        registry.register(first)
        registry.register(second)

        assert registry.exists("EAF-001")
        assert registry.get("EAF-001") == first
        assert [item.asset_id for item in registry.list_assets()] == ["EAF-001", "EAF-002"]

        registry.remove("EAF-001")
        assert not registry.exists("EAF-001")

    def test_duplicate_prevention(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(_asset("EAF-dup"))

        with pytest.raises(DuplicateEngineeringAssetError):
            registry.register(_asset("EAF-dup"))

    def test_missing_asset_raises_clear_error(self) -> None:
        registry = EngineeringAssetRegistry()

        with pytest.raises(EngineeringAssetNotFoundError, match="EAF-missing"):
            registry.get("EAF-missing")

    def test_find_by_vendor(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(_asset("EAF-001", vendor="Cisco"))
        registry.register(_asset("EAF-002", vendor="Microsoft"))

        results = registry.find_by_vendor("cisco")

        assert len(results) == 1
        assert results[0].asset_id == "EAF-001"

    def test_find_by_product(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(_asset("EAF-001", product="CUBE"))
        registry.register(_asset("EAF-002", product="SBC"))

        results = registry.find_by_product("cube")

        assert len(results) == 1
        assert results[0].asset_id == "EAF-001"

    def test_find_by_type(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(_asset("EAF-001", asset_type=EngineeringAssetType.RUNBOOK))
        registry.register(_asset("EAF-002", asset_type=EngineeringAssetType.BUG))

        results = registry.find_by_type(EngineeringAssetType.RUNBOOK)

        assert [item.asset_id for item in results] == ["EAF-001"]

    def test_find_by_tag(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(_asset("EAF-001", tags=("sip", "tls")))
        registry.register(_asset("EAF-002", tags=("monitoring",)))

        results = registry.find_by_tag("TLS")

        assert len(results) == 1
        assert results[0].asset_id == "EAF-001"


class TestEngineeringAssetLoader:
    def test_loader_reads_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "asset.yaml"
        path.write_text(
            "\n".join(
                [
                    "asset_id: EAF-yaml-001",
                    "title: Verification Guide",
                    "asset_type: VERIFICATION_GUIDE",
                    "category: SIP",
                    "vendor: ExampleVendor",
                    "product: ExampleProduct",
                    "summary: Verify SIP registration",
                    "description: Step-by-step verification",
                    "tags:",
                    "  - sip",
                    "  - registration",
                    "confidence: 0.9",
                    "created_at: '2026-06-19T12:00:00+00:00'",
                ]
            ),
            encoding="utf-8",
        )

        asset = EngineeringAssetLoader().load_file(path)

        assert asset.asset_id == "EAF-yaml-001"
        assert asset.asset_type == EngineeringAssetType.VERIFICATION_GUIDE
        assert asset.category == EngineeringCategory.SIP
        assert asset.tags == ("sip", "registration")

    def test_loader_validates_required_fields(self) -> None:
        with pytest.raises(EngineeringAssetValidationError, match="Missing required"):
            EngineeringAssetLoader().load_dict({"title": "Incomplete"})


class TestEngineeringAssetSearch:
    def test_search_text_vendor_product_tag_category_and_type(self) -> None:
        registry = EngineeringAssetRegistry()
        registry.register(
            EngineeringAsset(
                asset_id="EAF-001",
                title="SIP Verification Guide",
                asset_type=EngineeringAssetType.VERIFICATION_GUIDE,
                category=EngineeringCategory.SIP,
                vendor="Cisco",
                product="CUBE",
                version="1.0",
                summary="Verify SIP registration and TLS settings",
                description="Description for EAF-001",
                tags=("registration",),
                references=(),
                related_asset_ids=(),
                metadata={},
                created_at=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
                status=EngineeringAssetStatus.ACTIVE,
                source="unit-test",
                confidence=0.95,
            )
        )
        registry.register(
            _asset(
                "EAF-002",
                vendor="Microsoft",
                product="Teams",
                asset_type=EngineeringAssetType.DOCUMENT,
                category=EngineeringCategory.COLLABORATION,
                tags=("monitoring",),
            )
        )
        search = EngineeringAssetSearch(registry)

        assert search.search_text("verification")[0].asset_id == "EAF-001"
        assert search.search_vendor("Cisco")[0].asset_id == "EAF-001"
        assert search.search_product("CUBE")[0].asset_id == "EAF-001"
        assert search.search_tag("registration")[0].asset_id == "EAF-001"
        assert search.search_category(EngineeringCategory.SIP)[0].asset_id == "EAF-001"
        assert (
            search.search_type(EngineeringAssetType.VERIFICATION_GUIDE)[0].asset_id
            == "EAF-001"
        )


class TestEngineeringRelationships:
    def test_register_and_query_relationships(self) -> None:
        relationships = EngineeringRelationshipRegistry()
        relationship = EngineeringRelationship(
            source_asset="EAF-001",
            target_asset="EAF-002",
            relationship_type=EngineeringRelationshipType.VERIFIES,
        )

        relationships.register(relationship)

        listed = relationships.list_relationships()
        assert listed == (relationship,)
        assert relationships.find_for_asset("EAF-001") == (relationship,)
        assert relationships.find_by_type(EngineeringRelationshipType.VERIFIES) == (relationship,)

    def test_duplicate_relationship_prevention(self) -> None:
        relationships = EngineeringRelationshipRegistry()
        relationship = EngineeringRelationship(
            source_asset="EAF-001",
            target_asset="EAF-002",
            relationship_type=EngineeringRelationshipType.REFERENCES,
        )
        relationships.register(relationship)

        with pytest.raises(DuplicateEngineeringRelationshipError):
            relationships.register(relationship)


class TestEngineeringAssetReport:
    def test_markdown_report_includes_counts(self) -> None:
        registry = EngineeringAssetRegistry()
        relationships = EngineeringRelationshipRegistry()
        registry.register(_asset("EAF-001", vendor="Cisco", asset_type=EngineeringAssetType.RUNBOOK))
        registry.register(_asset("EAF-002", vendor="Cisco", asset_type=EngineeringAssetType.BUG))
        registry.register(_asset("EAF-003", vendor="Microsoft", asset_type=EngineeringAssetType.DOCUMENT))
        relationships.register(
            EngineeringRelationship(
                source_asset="EAF-001",
                target_asset="EAF-002",
                relationship_type=EngineeringRelationshipType.REFERENCES,
            )
        )

        markdown = EngineeringAssetReport(registry, relationships).to_markdown()

        assert "# Engineering Asset Framework Report" in markdown
        assert "**Total Assets:** 3" in markdown
        assert "**Total Relationships:** 1" in markdown
        assert "**RUNBOOK:** 1" in markdown
        assert "**BUG:** 1" in markdown
        assert "**Cisco:** 2" in markdown
        assert "**Microsoft:** 1" in markdown
        assert "**REFERENCES:** 1" in markdown
