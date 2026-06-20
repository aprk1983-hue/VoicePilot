"""Configuration diff data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from shared.types import JsonDict


class DiffChangeType(str, Enum):
    """Type of change detected between snapshot objects."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class DiffRiskLevel(str, Enum):
    """Aggregate risk level for a configuration diff."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ObjectDiff:
    """Object-level difference between two snapshot captures."""

    object_id: str
    object_type: str
    object_name: str
    change_type: DiffChangeType
    before_hash: str | None = None
    after_hash: str | None = None
    changed_fields: tuple[str, ...] = ()
    before: JsonDict | None = None
    after: JsonDict | None = None
    severity: str = "NONE"
    summary: str = ""


@dataclass(frozen=True)
class SnapshotDiff:
    """Deterministic diff between two configuration snapshots."""

    before_snapshot_id: str
    after_snapshot_id: str
    before_timestamp: datetime
    after_timestamp: datetime
    added: tuple[ObjectDiff, ...] = ()
    removed: tuple[ObjectDiff, ...] = ()
    modified: tuple[ObjectDiff, ...] = ()
    unchanged_count: int = 0
    summary: str = ""
    risk_level: str = DiffRiskLevel.NONE.value
