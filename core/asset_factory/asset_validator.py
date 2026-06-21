"""Deterministic validation for engineering asset production."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asset_factory.asset_exceptions import (
    AssetFactoryValidationError,
    DuplicateAssetIdError,
    DuplicateAssetTitleError,
    MissingRelatedAssetError,
)
from asset_factory.asset_templates import REQUIRED_FACTORY_FIELDS
from engineering_assets.asset_categories import EngineeringCategory
from engineering_assets.asset_models import EngineeringAsset, EngineeringAssetStatus
from engineering_assets.asset_types import EngineeringAssetType


@dataclass(frozen=True)
class ValidationIssue:
    """Single validation finding for an asset."""

    field: str
    message: str
    level: str  # error | warning


@dataclass(frozen=True)
class AssetValidationReport:
    """Validation outcome for one asset."""

    asset_id: str | None
    valid: bool
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class BatchValidationReport:
    """Validation outcome for a batch of assets."""

    valid: bool
    asset_reports: tuple[AssetValidationReport, ...]
    duplicate_ids: tuple[str, ...]
    duplicate_titles: tuple[str, ...]


class AssetValidator:
    """Validate structured asset data before production."""

    def validate_dict(
        self,
        data: dict[str, Any],
        *,
        known_asset_ids: frozenset[str] | None = None,
    ) -> AssetValidationReport:
        """Validate one structured asset dictionary."""
        issues: list[ValidationIssue] = []
        asset_id = str(data["asset_id"]) if data.get("asset_id") else None

        for field in REQUIRED_FACTORY_FIELDS:
            value = data.get(field)
            if value in (None, ""):
                issues.append(
                    ValidationIssue(
                        field=field,
                        message=f"Required field {field!r} is missing or empty",
                        level="error",
                    )
                )

        if data.get("asset_id") and not _is_non_empty_string(data["asset_id"]):
            issues.append(
                ValidationIssue(field="asset_id", message="asset_id must be a non-empty string", level="error")
            )

        if data.get("title") and not _is_non_empty_string(data["title"]):
            issues.append(
                ValidationIssue(field="title", message="title must be a non-empty string", level="error")
            )

        if "asset_type" in data:
            try:
                EngineeringAssetType(str(data["asset_type"]))
            except ValueError:
                issues.append(
                    ValidationIssue(
                        field="asset_type",
                        message=f"Invalid asset_type: {data['asset_type']!r}",
                        level="error",
                    )
                )

        if "category" in data and data["category"] not in (None, ""):
            try:
                EngineeringCategory(str(data["category"]))
            except ValueError:
                issues.append(
                    ValidationIssue(
                        field="category",
                        message=f"Invalid category: {data['category']!r}",
                        level="error",
                    )
                )

        if "status" in data and data["status"] not in (None, ""):
            try:
                EngineeringAssetStatus(str(data["status"]))
            except ValueError:
                issues.append(
                    ValidationIssue(
                        field="status",
                        message=f"Invalid status: {data['status']!r}",
                        level="error",
                    )
                )

        if "version" in data and data["version"] in (None, ""):
            issues.append(
                ValidationIssue(field="version", message="version must be present", level="error")
            )

        references = data.get("references", [])
        if references is not None and not isinstance(references, (list, tuple)):
            issues.append(
                ValidationIssue(field="references", message="references must be a list", level="error")
            )
        elif not references:
            issues.append(
                ValidationIssue(
                    field="references",
                    message="At least one reference is recommended",
                    level="warning",
                )
            )

        related_ids = _related_asset_ids(data)
        if known_asset_ids is not None and asset_id is not None:
            for related_id in related_ids:
                if related_id not in known_asset_ids and related_id != asset_id:
                    issues.append(
                        ValidationIssue(
                            field="related_asset_ids",
                            message=f"Related asset not found: {related_id}",
                            level="error",
                        )
                    )

        valid = not any(issue.level == "error" for issue in issues)
        return AssetValidationReport(
            asset_id=asset_id,
            valid=valid,
            issues=tuple(issues),
        )

    def validate_asset(
        self,
        asset: EngineeringAsset,
        *,
        known_asset_ids: frozenset[str] | None = None,
    ) -> AssetValidationReport:
        """Validate a built engineering asset."""
        data = _asset_to_dict(asset)
        return self.validate_dict(data, known_asset_ids=known_asset_ids)

    def validate_batch(
        self,
        items: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    ) -> BatchValidationReport:
        """Validate a batch with duplicate and cross-reference checks."""
        duplicate_ids = _find_duplicates(str(item["asset_id"]) for item in items if item.get("asset_id"))
        duplicate_titles = _find_duplicates(str(item["title"]) for item in items if item.get("title"))
        known_ids = frozenset(str(item["asset_id"]) for item in items if item.get("asset_id"))

        reports: list[AssetValidationReport] = []
        for item in items:
            report = self.validate_dict(item, known_asset_ids=known_ids)
            reports.append(report)

        batch_valid = (
            not duplicate_ids
            and not duplicate_titles
            and all(report.valid for report in reports)
        )
        return BatchValidationReport(
            valid=batch_valid,
            asset_reports=tuple(reports),
            duplicate_ids=duplicate_ids,
            duplicate_titles=duplicate_titles,
        )

    def validate_assets(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> BatchValidationReport:
        """Validate built engineering assets."""
        known_ids = frozenset(asset.asset_id for asset in assets)
        reports = tuple(
            self.validate_asset(asset, known_asset_ids=known_ids) for asset in assets
        )
        duplicate_ids = _find_duplicates(asset.asset_id for asset in assets)
        duplicate_titles = _find_duplicates(asset.title for asset in assets)
        batch_valid = (
            not duplicate_ids
            and not duplicate_titles
            and all(report.valid for report in reports)
        )
        return BatchValidationReport(
            valid=batch_valid,
            asset_reports=reports,
            duplicate_ids=duplicate_ids,
            duplicate_titles=duplicate_titles,
        )

    def assert_valid_dict(self, data: dict[str, Any], *, known_asset_ids: frozenset[str] | None = None) -> None:
        """Raise when validation fails."""
        report = self.validate_dict(data, known_asset_ids=known_asset_ids)
        if not report.valid:
            messages = "; ".join(issue.message for issue in report.issues if issue.level == "error")
            raise AssetFactoryValidationError(messages or "Validation failed", asset_id=report.asset_id)

    def assert_valid_batch(self, items: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> None:
        """Raise when batch validation fails."""
        report = self.validate_batch(items)
        if report.duplicate_ids:
            raise DuplicateAssetIdError(report.duplicate_ids[0])
        if report.duplicate_titles:
            raise DuplicateAssetTitleError(report.duplicate_titles[0])
        for asset_report in report.asset_reports:
            if not asset_report.valid:
                messages = "; ".join(
                    issue.message for issue in asset_report.issues if issue.level == "error"
                )
                raise AssetFactoryValidationError(
                    messages or "Validation failed",
                    asset_id=asset_report.asset_id,
                )
        for item in items:
            asset_id = str(item.get("asset_id", ""))
            for related_id in _related_asset_ids(item):
                known = frozenset(str(i["asset_id"]) for i in items if i.get("asset_id"))
                if related_id not in known:
                    raise MissingRelatedAssetError(asset_id, related_id)


def _asset_to_dict(asset: EngineeringAsset) -> dict[str, Any]:
    data: dict[str, Any] = {
        "asset_id": asset.asset_id,
        "title": asset.title,
        "asset_type": asset.asset_type.value,
        "category": asset.category.value,
        "vendor": asset.vendor,
        "product": asset.product,
        "version": asset.version,
        "summary": asset.summary,
        "description": asset.description,
        "tags": list(asset.tags),
        "references": list(asset.references),
        "related_asset_ids": list(asset.related_asset_ids),
        "status": asset.status.value,
        "confidence": asset.confidence,
        "metadata": dict(asset.metadata),
    }
    for key, value in asset.metadata.items():
        data[key] = value
    return data


def _related_asset_ids(data: dict[str, Any]) -> tuple[str, ...]:
    value = data.get("related_asset_ids", ())
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _find_duplicates(values: Any) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(sorted(duplicates))


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
