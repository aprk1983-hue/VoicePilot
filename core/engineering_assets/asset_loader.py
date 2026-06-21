"""YAML loader for engineering assets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engineering_assets.asset_categories import EngineeringCategory
from engineering_assets.asset_exceptions import EngineeringAssetValidationError
from engineering_assets.asset_models import EngineeringAsset, EngineeringAssetStatus
from engineering_assets.asset_types import EngineeringAssetType
from infrastructure.yaml_loader import YamlLoader


_REQUIRED_FIELDS = (
    "asset_id",
    "title",
    "asset_type",
    "category",
    "summary",
)

_METADATA_EXTENSION_FIELDS = (
    "severity",
    "symptoms",
    "required_evidence",
    "expected_findings",
    "expected_hypotheses",
    "related_health_rules",
    "related_discovery_rules",
    "related_knowledge_packs",
    "recommended_actions",
    "verification_steps",
)


class EngineeringAssetLoader:
    """Load vendor-neutral engineering assets from YAML documents."""

    def __init__(self, yaml_loader: YamlLoader | None = None) -> None:
        self._yaml_loader = yaml_loader or YamlLoader()

    def load_file(self, path: Path) -> EngineeringAsset:
        """Load and validate an engineering asset from a YAML file."""
        data = self._yaml_loader.load_file(path)
        return self.load_dict(data, source=str(path))

    def load_dict(self, data: dict[str, Any], *, source: str = "yaml") -> EngineeringAsset:
        """Load and validate an engineering asset from a mapping."""
        missing = [field for field in _REQUIRED_FIELDS if field not in data or data[field] in (None, "")]
        if missing:
            raise EngineeringAssetValidationError(
                f"Missing required engineering asset fields: {', '.join(missing)}"
            )

        try:
            asset_type = EngineeringAssetType(str(data["asset_type"]))
        except ValueError as exc:
            raise EngineeringAssetValidationError(
                f"Invalid asset_type: {data['asset_type']!r}"
            ) from exc

        try:
            category = EngineeringCategory(str(data["category"]))
        except ValueError as exc:
            raise EngineeringAssetValidationError(
                f"Invalid category: {data['category']!r}"
            ) from exc

        status_value = str(data.get("status", EngineeringAssetStatus.ACTIVE.value))
        try:
            status = EngineeringAssetStatus(status_value)
        except ValueError as exc:
            raise EngineeringAssetValidationError(f"Invalid status: {status_value!r}") from exc

        created_at = _parse_datetime(data.get("created_at"))
        updated_at = _parse_datetime(data.get("updated_at"), fallback=created_at)

        confidence = data.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)):
            raise EngineeringAssetValidationError("confidence must be numeric")

        metadata = dict(data.get("metadata", {})) if isinstance(data.get("metadata", {}), dict) else {}
        if not isinstance(data.get("metadata", {}), dict) and "metadata" in data:
            raise EngineeringAssetValidationError("metadata must be a mapping")
        for field_name in _METADATA_EXTENSION_FIELDS:
            if field_name in data:
                metadata[field_name] = data[field_name]

        return EngineeringAsset(
            asset_id=str(data["asset_id"]),
            title=str(data["title"]),
            asset_type=asset_type,
            category=category,
            vendor=str(data.get("vendor", "")),
            product=str(data.get("product", "")),
            version=str(data.get("version", "")),
            summary=str(data["summary"]),
            description=str(data.get("description", "")),
            tags=_to_string_tuple(data.get("tags", [])),
            references=_to_string_tuple(data.get("references", [])),
            related_asset_ids=_to_string_tuple(data.get("related_asset_ids", [])),
            metadata=dict(metadata),
            created_at=created_at,
            updated_at=updated_at,
            status=status,
            source=str(data.get("source", source)),
            confidence=float(confidence),
        )


def _to_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise EngineeringAssetValidationError("Expected a list for sequence fields")
    return tuple(str(item) for item in value)


def _parse_datetime(value: Any, *, fallback: datetime | None = None) -> datetime:
    if value is None:
        if fallback is not None:
            return fallback
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    raise EngineeringAssetValidationError("created_at/updated_at must be ISO-8601 strings")
