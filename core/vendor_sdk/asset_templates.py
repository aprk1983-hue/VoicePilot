"""Vendor-neutral asset templates for SDK generation."""

from __future__ import annotations

from engineering_assets.asset_types import EngineeringAssetType
from vendor_sdk.vendor_models import AssetTemplate

ASSET_TEMPLATES: tuple[AssetTemplate, ...] = (
    AssetTemplate(
        asset_type=EngineeringAssetType.INCIDENT,
        filename_suffix="incident.yaml",
        id_suffix="{sequence:06d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "symptoms",
            "expected_findings",
            "known_causes",
            "known_resolution",
            "recommended_actions",
            "verification_steps",
            "rollback_steps",
            "references",
            "related_asset_ids",
        ),
        default_category="GENERAL",
    ),
    AssetTemplate(
        asset_type=EngineeringAssetType.RUNBOOK,
        filename_suffix="runbook.yaml",
        id_suffix="RB-{sequence:03d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "recommended_actions",
            "verification_steps",
            "rollback_steps",
            "references",
            "related_asset_ids",
        ),
    ),
    AssetTemplate(
        asset_type=EngineeringAssetType.VERIFICATION_GUIDE,
        filename_suffix="verification.yaml",
        id_suffix="VG-{sequence:03d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "required_evidence",
            "verification_steps",
            "references",
            "related_asset_ids",
        ),
    ),
    AssetTemplate(
        asset_type=EngineeringAssetType.REFERENCE,
        filename_suffix="reference.yaml",
        id_suffix="REF-{sequence:03d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "references",
            "related_asset_ids",
        ),
    ),
    AssetTemplate(
        asset_type=EngineeringAssetType.BEST_PRACTICE,
        filename_suffix="best_practice.yaml",
        id_suffix="BP-{sequence:03d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "recommended_actions",
            "references",
            "related_asset_ids",
        ),
    ),
    AssetTemplate(
        asset_type=EngineeringAssetType.BUG,
        filename_suffix="bug.yaml",
        id_suffix="BUG-{sequence:03d}",
        required_fields=(
            "asset_id",
            "title",
            "asset_type",
            "category",
            "vendor",
            "product",
            "version",
            "summary",
            "status",
            "severity",
            "known_causes",
            "known_resolution",
            "references",
            "related_asset_ids",
        ),
    ),
)

TEMPLATE_BY_TYPE: dict[EngineeringAssetType, AssetTemplate] = {
    template.asset_type: template for template in ASSET_TEMPLATES
}

PACKAGE_ASSET_TYPES: tuple[EngineeringAssetType, ...] = tuple(
    template.asset_type for template in ASSET_TEMPLATES
)

MIN_QUALITY_SCORE = 95
