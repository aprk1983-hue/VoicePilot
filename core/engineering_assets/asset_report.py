"""Markdown reporting for engineering asset collections."""

from __future__ import annotations

from collections import Counter

from engineering_assets.asset_models import EngineeringAssetSnapshot
from engineering_assets.asset_registry import EngineeringAssetRegistry
from engineering_assets.asset_relationships import EngineeringRelationshipRegistry


class EngineeringAssetReport:
    """Build markdown summaries for engineering asset collections."""

    def __init__(
        self,
        registry: EngineeringAssetRegistry,
        relationship_registry: EngineeringRelationshipRegistry | None = None,
    ) -> None:
        self._registry = registry
        self._relationship_registry = relationship_registry

    def snapshot(self) -> EngineeringAssetSnapshot:
        """Return a snapshot of assets and relationships."""
        relationships = ()
        if self._relationship_registry is not None:
            relationships = self._relationship_registry.list_relationships()
        return EngineeringAssetSnapshot(
            assets=self._registry.list_assets(),
            relationships=relationships,
        )

    def to_markdown(self) -> str:
        """Render a markdown summary of the current asset collection."""
        snapshot = self.snapshot()
        assets = snapshot.assets
        relationships = snapshot.relationships

        vendor_counts = Counter(asset.vendor or "(unspecified)" for asset in assets)
        type_counts = Counter(asset.asset_type.value for asset in assets)
        relationship_counts = Counter(
            relationship.relationship_type.value for relationship in relationships
        )

        lines = [
            "# Engineering Asset Framework Report",
            "",
            "## Summary",
            "",
            f"- **Total Assets:** {len(assets)}",
            f"- **Total Relationships:** {len(relationships)}",
            "",
            "## Asset Counts by Type",
            "",
        ]

        if type_counts:
            for asset_type, count in sorted(type_counts.items()):
                lines.append(f"- **{asset_type}:** {count}")
        else:
            lines.append("_No assets registered._")

        lines.extend(["", "## Vendor Counts", ""])
        if vendor_counts:
            for vendor, count in sorted(vendor_counts.items()):
                lines.append(f"- **{vendor}:** {count}")
        else:
            lines.append("_No vendors recorded._")

        lines.extend(["", "## Relationship Counts", ""])
        if relationship_counts:
            for relationship_type, count in sorted(relationship_counts.items()):
                lines.append(f"- **{relationship_type}:** {count}")
        else:
            lines.append("_No relationships registered._")

        return "\n".join(lines)
