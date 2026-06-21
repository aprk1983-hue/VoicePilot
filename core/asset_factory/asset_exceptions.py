"""Exceptions for the Engineering Asset Factory."""


class AssetFactoryError(Exception):
    """Base error for asset factory operations."""


class AssetFactoryValidationError(AssetFactoryError):
    """Raised when structured asset data fails factory validation."""

    def __init__(self, message: str, *, asset_id: str | None = None) -> None:
        self.asset_id = asset_id
        super().__init__(message)


class DuplicateAssetIdError(AssetFactoryError):
    """Raised when duplicate asset IDs are detected in a batch."""

    def __init__(self, asset_id: str) -> None:
        self.asset_id = asset_id
        super().__init__(f"Duplicate asset ID: {asset_id}")


class DuplicateAssetTitleError(AssetFactoryError):
    """Raised when duplicate asset titles are detected in a batch."""

    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"Duplicate asset title: {title!r}")


class MissingRelatedAssetError(AssetFactoryError):
    """Raised when a related asset ID does not exist in the batch or registry."""

    def __init__(self, asset_id: str, related_asset_id: str) -> None:
        self.asset_id = asset_id
        self.related_asset_id = related_asset_id
        super().__init__(
            f"Asset {asset_id!r} references missing related asset {related_asset_id!r}"
        )
