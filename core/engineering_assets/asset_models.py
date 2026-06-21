"""Engineering Asset Framework domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from engineering_assets.asset_categories import EngineeringCategory
from engineering_assets.asset_types import EngineeringAssetType


class EngineeringAssetStatus(str, Enum):
    """Lifecycle status for an engineering asset."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class EngineeringRelationshipType(str, Enum):
    """Typed links between engineering assets."""

    RELATED_TO = "RELATED_TO"
    REFERENCES = "REFERENCES"
    SUPERSEDES = "SUPERSEDES"
    REQUIRES = "REQUIRES"
    VERIFIES = "VERIFIES"
    IMPLEMENTS = "IMPLEMENTS"
    DOCUMENTS = "DOCUMENTS"
    KNOWN_ISSUE = "KNOWN_ISSUE"
    FIXES = "FIXES"
    DUPLICATE_OF = "DUPLICATE_OF"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EngineeringAsset:
    """Immutable vendor-neutral engineering knowledge asset."""

    asset_id: str
    title: str
    asset_type: EngineeringAssetType
    category: EngineeringCategory
    vendor: str
    product: str
    version: str
    summary: str
    description: str
    tags: tuple[str, ...]
    references: tuple[str, ...]
    related_asset_ids: tuple[str, ...]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    status: EngineeringAssetStatus
    source: str
    confidence: float


@dataclass(frozen=True)
class EngineeringRelationship:
    """Immutable typed relationship between two engineering assets."""

    source_asset: str
    target_asset: str
    relationship_type: EngineeringRelationshipType


@dataclass(frozen=True)
class EngineeringAssetSnapshot:
    """Registry snapshot used for reporting and search indexing."""

    assets: tuple[EngineeringAsset, ...] = field(default_factory=tuple)
    relationships: tuple[EngineeringRelationship, ...] = field(default_factory=tuple)
