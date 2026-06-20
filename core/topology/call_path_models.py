"""Call path models for deterministic voice topology traversal."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from shared.types import JsonDict


class CallPathDirection(str, Enum):
    """Direction of a modeled call path."""

    OUTBOUND = "outbound"
    INBOUND = "inbound"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CallPathHop:
    """Single hop in a modeled call path."""

    object_id: str
    object_type: str
    label: str
    relationship_to_next: str | None
    health_status: str
    findings: tuple[str, ...] = field(default_factory=tuple)
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class CallPath:
    """Deterministic call path between two topology objects."""

    id: str
    direction: CallPathDirection
    source_object_id: str
    destination_object_id: str
    hops: tuple[CallPathHop, ...]
    summary: str
    warnings: tuple[str, ...] = field(default_factory=tuple)
