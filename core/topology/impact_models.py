"""Impact analysis result models for voice topology graphs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from model.voice_graph import VoiceObject, VoiceRelationship


class ImpactSeverity(str, Enum):
    """Operational impact severity derived from dependent object counts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ImpactDependencyPath:
    """Directed dependency path from an impacted object to the affected object."""

    impacted_object_id: str
    relationships: tuple[VoiceRelationship, ...]


@dataclass(frozen=True)
class ImpactReport:
    """Deterministic impact assessment for a topology object change or failure."""

    affected_object: VoiceObject
    severity: ImpactSeverity
    impacted_objects: tuple[VoiceObject, ...]
    dependency_paths: tuple[ImpactDependencyPath, ...]
    summary: str
    recommendations: tuple[str, ...]
