"""Engineering asset relationship registry."""

from __future__ import annotations

from engineering_assets.asset_exceptions import (
    DuplicateEngineeringRelationshipError,
    EngineeringRelationshipNotFoundError,
)
from engineering_assets.asset_models import EngineeringRelationship, EngineeringRelationshipType


class EngineeringRelationshipRegistry:
    """Store and query typed relationships between engineering assets."""

    def __init__(self) -> None:
        self._relationships: dict[tuple[str, str, EngineeringRelationshipType], EngineeringRelationship] = {}

    def register(self, relationship: EngineeringRelationship) -> EngineeringRelationship:
        """Register a relationship, preventing exact duplicates."""
        key = (
            relationship.source_asset,
            relationship.target_asset,
            relationship.relationship_type,
        )
        if key in self._relationships:
            raise DuplicateEngineeringRelationshipError(
                relationship.source_asset,
                relationship.target_asset,
                relationship.relationship_type.value,
            )
        self._relationships[key] = relationship
        return relationship

    def remove(
        self,
        source_asset: str,
        target_asset: str,
        relationship_type: EngineeringRelationshipType,
    ) -> None:
        """Remove a relationship from the registry."""
        key = (source_asset, target_asset, relationship_type)
        if key not in self._relationships:
            raise EngineeringRelationshipNotFoundError(
                source_asset,
                target_asset,
                relationship_type.value,
            )
        del self._relationships[key]

    def list_relationships(self) -> tuple[EngineeringRelationship, ...]:
        """Return all relationships in deterministic order."""
        return tuple(
            self._relationships[key]
            for key in sorted(
                self._relationships,
                key=lambda item: (item[0], item[1], item[2].value),
            )
        )

    def find_for_asset(self, asset_id: str) -> tuple[EngineeringRelationship, ...]:
        """Return relationships where the asset is source or target."""
        return tuple(
            relationship
            for relationship in self.list_relationships()
            if relationship.source_asset == asset_id or relationship.target_asset == asset_id
        )

    def find_by_type(
        self,
        relationship_type: EngineeringRelationshipType,
    ) -> tuple[EngineeringRelationship, ...]:
        """Return relationships of a given type."""
        return tuple(
            relationship
            for relationship in self.list_relationships()
            if relationship.relationship_type == relationship_type
        )
