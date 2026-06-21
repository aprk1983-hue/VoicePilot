"""Deterministic search over engineering assets."""

from __future__ import annotations

from engineering_assets.asset_categories import EngineeringCategory
from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_registry import EngineeringAssetRegistry
from engineering_assets.asset_types import EngineeringAssetType


class EngineeringAssetSearch:
    """Simple deterministic filtering over an engineering asset registry."""

    def __init__(self, registry: EngineeringAssetRegistry) -> None:
        self._registry = registry

    def search_text(self, query: str) -> tuple[EngineeringAsset, ...]:
        """Search title, summary, description, and tags for a text query."""
        normalized = query.strip().lower()
        if not normalized:
            return self._registry.list_assets()

        results: list[EngineeringAsset] = []
        for asset in self._registry.list_assets():
            haystack = " ".join(
                [
                    asset.title,
                    asset.summary,
                    asset.description,
                    " ".join(asset.tags),
                ]
            ).lower()
            if normalized in haystack:
                results.append(asset)
        return tuple(results)

    def search_vendor(self, vendor: str) -> tuple[EngineeringAsset, ...]:
        """Return assets for a vendor."""
        return self._registry.find_by_vendor(vendor)

    def search_product(self, product: str) -> tuple[EngineeringAsset, ...]:
        """Return assets for a product."""
        return self._registry.find_by_product(product)

    def search_tag(self, tag: str) -> tuple[EngineeringAsset, ...]:
        """Return assets containing a tag."""
        return self._registry.find_by_tag(tag)

    def search_category(self, category: EngineeringCategory) -> tuple[EngineeringAsset, ...]:
        """Return assets in a category."""
        return tuple(
            asset for asset in self._registry.list_assets() if asset.category == category
        )

    def search_type(self, asset_type: EngineeringAssetType) -> tuple[EngineeringAsset, ...]:
        """Return assets of a given type."""
        return self._registry.find_by_type(asset_type)
