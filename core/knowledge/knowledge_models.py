"""Core VKF data models."""

from __future__ import annotations

from dataclasses import dataclass, field

from knowledge.knowledge_categories import KnowledgeCategory
from knowledge.knowledge_severity import KnowledgeSeverity
from shared.types import JsonDict


@dataclass(frozen=True)
class KnowledgeMatch:
    """A knowledge pack matched to a canonical voice object."""

    pack_id: str
    object_id: str
    object_type: str
    title: str
    category: KnowledgeCategory
    severity: KnowledgeSeverity
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class KnowledgePack:
    """Structured vendor-neutral knowledge entry."""

    id: str
    title: str
    description: str
    vendor: str
    platform: str
    category: KnowledgeCategory
    severity: KnowledgeSeverity
    supported_object_types: tuple[str, ...]
    conditions: JsonDict
    recommendations: tuple[str, ...]
    references: tuple[str, ...] = field(default_factory=tuple)
    metadata: JsonDict = field(default_factory=dict)
    version: str = "1.0"
