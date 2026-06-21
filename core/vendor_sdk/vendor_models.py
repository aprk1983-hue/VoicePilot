"""Immutable models for the Vendor Asset SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from engineering_assets.asset_types import EngineeringAssetType


@dataclass(frozen=True)
class VendorDefinition:
    """Registered vendor metadata."""

    vendor_id: str
    name: str
    slug: str
    description: str = ""


@dataclass(frozen=True)
class ProductDefinition:
    """Registered product under a vendor."""

    product_id: str
    vendor_id: str
    name: str
    slug: str
    default_category: str = "GENERAL"
    description: str = ""


@dataclass(frozen=True)
class AssetTemplate:
    """Template definition for one engineering asset type."""

    asset_type: EngineeringAssetType
    filename_suffix: str
    id_suffix: str
    required_fields: tuple[str, ...]
    default_category: str = "GENERAL"


@dataclass(frozen=True)
class AssetBlueprint:
    """Generated asset identifiers and relationships for one package."""

    package_key: str
    vendor: VendorDefinition
    product: ProductDefinition
    title: str
    asset_ids: dict[str, str]
    related_asset_ids: tuple[str, ...]


@dataclass(frozen=True)
class AssetGenerationRequest:
    """Input for generating engineering assets."""

    vendor: str
    product: str
    title: str
    category: str = "GENERAL"
    severity: str = "high"
    summary: str | None = None
    symptoms: tuple[str, ...] = ()
    expected_findings: tuple[str, ...] = ()
    likely_causes: tuple[str, ...] = ()
    resolution: tuple[str, ...] = ()
    rollback: tuple[str, ...] = ()
    verification_steps: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    sequence: int = 1
    output_dir: Path | None = None


@dataclass(frozen=True)
class AssetGenerationResult:
    """Output from generating one or more assets."""

    blueprint: AssetBlueprint
    assets: tuple[dict[str, Any], ...]
    yaml_files: tuple[Path, ...]
    readme_path: Path | None
    quality_scores: dict[str, int]
    validation_passed: bool
    generated_at: datetime


@dataclass(frozen=True)
class VendorStatistics:
    """Aggregate SDK catalog statistics."""

    vendor_count: int
    product_count: int
    vendors: tuple[str, ...]
    products_by_vendor: dict[str, tuple[str, ...]]
