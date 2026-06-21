"""Engineering Knowledge Framework domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engineering_assets.asset_models import EngineeringAsset


class KnowledgeRelationshipType(str, Enum):
    """Typed links between engineering knowledge entries."""

    RELATED = "RELATED"
    DEPENDS_ON = "DEPENDS_ON"
    REFERENCES = "REFERENCES"
    SUPERSEDES = "SUPERSEDES"
    VERIFIES = "VERIFIES"
    IMPLEMENTS = "IMPLEMENTS"
    CAUSES = "CAUSES"
    RESOLVES = "RESOLVES"
    SIMILAR_TO = "SIMILAR_TO"
    KNOWN_WITH = "KNOWN_WITH"


@dataclass(frozen=True)
class EngineeringKnowledge:
    """Explainable engineering knowledge entry linked to assets."""

    knowledge_id: str
    title: str
    summary: str
    asset_ids: tuple[str, ...]
    tags: tuple[str, ...] = field(default_factory=tuple)
    match_signals: tuple[str, ...] = field(default_factory=tuple)
    match_object_types: tuple[str, ...] = field(default_factory=tuple)
    match_health_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "engineering-knowledge"
    confidence: float = 1.0


@dataclass(frozen=True)
class KnowledgeMatch:
    """Deterministic match between context and engineering knowledge."""

    knowledge_id: str
    title: str
    summary: str
    matched_asset_ids: tuple[str, ...]
    match_reason: str
    score: float
    match_source: str


@dataclass(frozen=True)
class KnowledgeRelationship:
    """Immutable typed relationship between knowledge entries."""

    source_knowledge_id: str
    target_knowledge_id: str
    relationship_type: KnowledgeRelationshipType


@dataclass(frozen=True)
class KnowledgeRecommendation:
    """Recommended reading derived from matched knowledge and assets."""

    knowledge_id: str
    title: str
    recommendation_type: str
    asset_id: str | None
    summary: str


@dataclass(frozen=True)
class KnowledgeReport:
    """Aggregated engineering knowledge evaluation result."""

    matches: tuple[KnowledgeMatch, ...]
    related_assets: tuple[EngineeringAsset, ...]
    recommendations: tuple[KnowledgeRecommendation, ...]
    summary: str
