"""Automatic relationship generation for engineering assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asset_factory.asset_templates import CHAIN_RELATIONSHIP_TYPES, RELATIONSHIP_CHAIN
from engineering_assets.asset_models import (
    EngineeringAsset,
    EngineeringRelationship,
    EngineeringRelationshipType,
)
from engineering_assets.asset_types import EngineeringAssetType


@dataclass(frozen=True)
class RelationshipBuildResult:
    """Relationships generated for one asset."""

    asset_id: str
    relationships: tuple[EngineeringRelationship, ...]


class AssetRelationshipBuilder:
    """Link assets using IDs already present in structured content."""

    def build_for_asset(
        self,
        asset: EngineeringAsset,
        *,
        assets_by_id: dict[str, EngineeringAsset],
    ) -> RelationshipBuildResult:
        """Generate relationships for one asset from related_asset_ids and chain rules."""
        relationships: list[EngineeringRelationship] = []
        seen: set[tuple[str, str, EngineeringRelationshipType]] = set()

        for related_id in asset.related_asset_ids:
            if related_id not in assets_by_id:
                continue
            related = assets_by_id[related_id]
            rel_type = _relationship_type_between(asset.asset_type, related.asset_type)
            key = (asset.asset_id, related_id, rel_type)
            if key not in seen:
                seen.add(key)
                relationships.append(
                    EngineeringRelationship(
                        source_asset=asset.asset_id,
                        target_asset=related_id,
                        relationship_type=rel_type,
                    )
                )

        chain_target = _next_chain_target(asset.asset_type, assets_by_id.values())
        if chain_target is not None and chain_target.asset_id not in asset.related_asset_ids:
            rel_type = _relationship_type_between(asset.asset_type, chain_target.asset_type)
            key = (asset.asset_id, chain_target.asset_id, rel_type)
            if key not in seen:
                seen.add(key)
                relationships.append(
                    EngineeringRelationship(
                        source_asset=asset.asset_id,
                        target_asset=chain_target.asset_id,
                        relationship_type=rel_type,
                    )
                )

        return RelationshipBuildResult(
            asset_id=asset.asset_id,
            relationships=tuple(
                sorted(relationships, key=lambda item: (item.source_asset, item.target_asset, item.relationship_type.value))
            ),
        )

    def build_batch(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> tuple[EngineeringRelationship, ...]:
        """Generate relationships for a batch of assets."""
        assets_by_id = {asset.asset_id: asset for asset in assets}
        all_relationships: list[EngineeringRelationship] = []
        seen: set[tuple[str, str, EngineeringRelationshipType]] = set()

        for asset in assets:
            result = self.build_for_asset(asset, assets_by_id=assets_by_id)
            for relationship in result.relationships:
                key = (
                    relationship.source_asset,
                    relationship.target_asset,
                    relationship.relationship_type,
                )
                if key not in seen:
                    seen.add(key)
                    all_relationships.append(relationship)

        return tuple(
            sorted(
                all_relationships,
                key=lambda item: (item.source_asset, item.target_asset, item.relationship_type.value),
            )
        )


def _relationship_type_between(
    source_type: EngineeringAssetType,
    target_type: EngineeringAssetType,
) -> EngineeringRelationshipType:
    key = (source_type, target_type)
    if key in CHAIN_RELATIONSHIP_TYPES:
        return EngineeringRelationshipType(CHAIN_RELATIONSHIP_TYPES[key])

    if target_type == EngineeringAssetType.BUG:
        return EngineeringRelationshipType.KNOWN_ISSUE
    if target_type == EngineeringAssetType.VERIFICATION_GUIDE:
        return EngineeringRelationshipType.VERIFIES
    if target_type == EngineeringAssetType.RUNBOOK:
        return EngineeringRelationshipType.IMPLEMENTS
    if target_type == EngineeringAssetType.REFERENCE:
        return EngineeringRelationshipType.REFERENCES
    return EngineeringRelationshipType.RELATED_TO


def _next_chain_target(
    asset_type: EngineeringAssetType,
    assets: Any,
) -> EngineeringAsset | None:
    try:
        index = RELATIONSHIP_CHAIN.index(asset_type)
    except ValueError:
        return None
    if index >= len(RELATIONSHIP_CHAIN) - 1:
        return None

    target_type = RELATIONSHIP_CHAIN[index + 1]
    candidates = [asset for asset in assets if asset.asset_type == target_type]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item.asset_id)[0]
