"""Deterministic asset ID generation for the Vendor Asset SDK."""

from __future__ import annotations

from engineering_assets.asset_types import EngineeringAssetType
from vendor_sdk.asset_templates import TEMPLATE_BY_TYPE


def build_asset_id(vendor_slug: str, product_slug: str, asset_type: EngineeringAssetType, sequence: int) -> str:
    """Return a vendor-neutral engineering asset identifier."""
    template = TEMPLATE_BY_TYPE[asset_type]
    suffix = template.id_suffix.format(sequence=sequence)
    return f"VP-{vendor_slug}-{product_slug}-{suffix}"


def slugify_title(title: str) -> str:
    """Convert a title into a filesystem-safe slug."""
    normalized = "".join(ch if ch.isalnum() else "-" for ch in title.lower())
    parts = [part for part in normalized.split("-") if part]
    return "-".join(parts) or "asset"
