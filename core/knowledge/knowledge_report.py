"""Aggregated knowledge evaluation report."""

from __future__ import annotations

from dataclasses import dataclass, field

from knowledge.knowledge_models import KnowledgeMatch


@dataclass(frozen=True)
class KnowledgeReport:
    """Aggregated knowledge matches for objects or a topology."""

    matched_packs: tuple[KnowledgeMatch, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "No knowledge packs matched."
