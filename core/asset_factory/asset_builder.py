"""Normalize structured dictionaries into production-ready engineering assets."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from asset_factory.asset_templates import (
    ASSET_TYPE_TEMPLATES,
    DEFAULT_PLACEHOLDERS,
    METADATA_EXTENSION_FIELDS,
)
from engineering_assets.asset_loader import EngineeringAssetLoader
from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_types import EngineeringAssetType


class AssetBuilder:
    """Build complete EngineeringAsset instances from structured dictionaries."""

    def __init__(self, loader: EngineeringAssetLoader | None = None) -> None:
        self._loader = loader or EngineeringAssetLoader()

    def normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply templates and placeholders to raw structured data."""
        normalized = deepcopy(data)
        for key, value in DEFAULT_PLACEHOLDERS.items():
            if key not in normalized or normalized[key] in (None, ""):
                normalized[key] = deepcopy(value)

        try:
            asset_type = EngineeringAssetType(str(normalized["asset_type"]))
        except (KeyError, ValueError):
            asset_type = None

        if asset_type is not None:
            template = ASSET_TYPE_TEMPLATES.get(asset_type, {})
            for key, value in template.items():
                current = normalized.get(key)
                if current in (None, "", []):
                    normalized[key] = deepcopy(value)

        if "created_at" not in normalized:
            normalized["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in normalized:
            normalized["updated_at"] = normalized["created_at"]

        metadata = dict(normalized.get("metadata", {})) if isinstance(normalized.get("metadata"), dict) else {}
        for field_name in METADATA_EXTENSION_FIELDS:
            if field_name in normalized and field_name not in metadata:
                metadata[field_name] = normalized[field_name]
        normalized["metadata"] = metadata

        return normalized

    def build(self, data: dict[str, Any], *, source: str = "factory") -> EngineeringAsset:
        """Normalize and load one engineering asset."""
        normalized = self.normalize(data)
        return self._loader.load_dict(normalized, source=source)

    def build_batch(
        self,
        items: tuple[dict[str, Any], ...] | list[dict[str, Any]],
        *,
        source: str = "factory",
    ) -> tuple[EngineeringAsset, ...]:
        """Build multiple assets in deterministic order."""
        return tuple(self.build(item, source=source) for item in items)
