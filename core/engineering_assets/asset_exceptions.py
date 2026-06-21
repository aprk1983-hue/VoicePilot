"""Engineering Asset Framework exceptions."""

from __future__ import annotations


class EngineeringAssetError(Exception):
    """Base exception for the Engineering Asset Framework."""


class DuplicateEngineeringAssetError(EngineeringAssetError):
    """Raised when registering an asset with an existing ID."""

    def __init__(self, asset_id: str) -> None:
        super().__init__(f"Engineering asset already registered: {asset_id}")
        self.asset_id = asset_id


class EngineeringAssetNotFoundError(EngineeringAssetError):
    """Raised when an asset ID is not registered."""

    def __init__(self, asset_id: str) -> None:
        super().__init__(f"Engineering asset not found: {asset_id}")
        self.asset_id = asset_id


class EngineeringAssetValidationError(EngineeringAssetError):
    """Raised when asset data fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DuplicateEngineeringRelationshipError(EngineeringAssetError):
    """Raised when registering a duplicate relationship."""

    def __init__(self, source_asset: str, target_asset: str, relationship_type: str) -> None:
        super().__init__(
            f"Relationship already registered: {source_asset} -> {target_asset} ({relationship_type})"
        )
        self.source_asset = source_asset
        self.target_asset = target_asset
        self.relationship_type = relationship_type


class EngineeringRelationshipNotFoundError(EngineeringAssetError):
    """Raised when a relationship cannot be found."""

    def __init__(self, source_asset: str, target_asset: str, relationship_type: str) -> None:
        super().__init__(
            f"Relationship not found: {source_asset} -> {target_asset} ({relationship_type})"
        )
