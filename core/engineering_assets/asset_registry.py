"""In-memory Engineering Asset registry."""

from __future__ import annotations

from engineering_assets.asset_exceptions import (
    DuplicateEngineeringAssetError,
    EngineeringAssetNotFoundError,
)
from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_types import EngineeringAssetType


class EngineeringAssetRegistry:
    """Store and query engineering assets in memory."""

    def __init__(self) -> None:
        self._assets: dict[str, EngineeringAsset] = {}

    def register(self, asset: EngineeringAsset) -> EngineeringAsset:
        """Register a new engineering asset, preventing duplicate IDs."""
        if asset.asset_id in self._assets:
            raise DuplicateEngineeringAssetError(asset.asset_id)
        self._assets[asset.asset_id] = asset
        return asset

    def remove(self, asset_id: str) -> None:
        """Remove an engineering asset from the registry."""
        if asset_id not in self._assets:
            raise EngineeringAssetNotFoundError(asset_id)
        del self._assets[asset_id]

    def get(self, asset_id: str) -> EngineeringAsset:
        """Return an engineering asset by ID."""
        asset = self._assets.get(asset_id)
        if asset is None:
            raise EngineeringAssetNotFoundError(asset_id)
        return asset

    def exists(self, asset_id: str) -> bool:
        """Return whether an asset ID is registered."""
        return asset_id in self._assets

    def list_assets(self) -> tuple[EngineeringAsset, ...]:
        """Return all assets in deterministic order."""
        return tuple(self._assets[asset_id] for asset_id in sorted(self._assets))

    def find_by_vendor(self, vendor: str) -> tuple[EngineeringAsset, ...]:
        """Return assets whose vendor matches case-insensitively."""
        normalized = vendor.strip().lower()
        return tuple(
            asset
            for asset in self.list_assets()
            if asset.vendor.strip().lower() == normalized
        )

    def find_by_product(self, product: str) -> tuple[EngineeringAsset, ...]:
        """Return assets whose product matches case-insensitively."""
        normalized = product.strip().lower()
        return tuple(
            asset
            for asset in self.list_assets()
            if asset.product.strip().lower() == normalized
        )

    def find_by_type(self, asset_type: EngineeringAssetType) -> tuple[EngineeringAsset, ...]:
        """Return assets of a given type."""
        return tuple(asset for asset in self.list_assets() if asset.asset_type == asset_type)

    def find_by_tag(self, tag: str) -> tuple[EngineeringAsset, ...]:
        """Return assets containing a tag case-insensitively."""
        normalized = tag.strip().lower()
        return tuple(
            asset
            for asset in self.list_assets()
            if any(item.strip().lower() == normalized for item in asset.tags)
        )
