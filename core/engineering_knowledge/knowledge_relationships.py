"""Knowledge relationship registry."""

from __future__ import annotations

from engineering_knowledge.knowledge_exceptions import (
    DuplicateKnowledgeRelationshipError,
    KnowledgeRelationshipNotFoundError,
)
from engineering_knowledge.knowledge_models import KnowledgeRelationship, KnowledgeRelationshipType


class KnowledgeRelationshipRegistry:
    """Store and query typed relationships between knowledge entries."""

    def __init__(self) -> None:
        self._relationships: dict[
            tuple[str, str, KnowledgeRelationshipType],
            KnowledgeRelationship,
        ] = {}

    def register(self, relationship: KnowledgeRelationship) -> KnowledgeRelationship:
        """Register a relationship, preventing exact duplicates."""
        key = (
            relationship.source_knowledge_id,
            relationship.target_knowledge_id,
            relationship.relationship_type,
        )
        if key in self._relationships:
            raise DuplicateKnowledgeRelationshipError(
                relationship.source_knowledge_id,
                relationship.target_knowledge_id,
                relationship.relationship_type.value,
            )
        self._relationships[key] = relationship
        return relationship

    def remove(
        self,
        source_knowledge_id: str,
        target_knowledge_id: str,
        relationship_type: KnowledgeRelationshipType,
    ) -> None:
        """Remove a relationship from the registry."""
        key = (source_knowledge_id, target_knowledge_id, relationship_type)
        if key not in self._relationships:
            raise KnowledgeRelationshipNotFoundError(
                source_knowledge_id,
                target_knowledge_id,
                relationship_type.value,
            )
        del self._relationships[key]

    def list_relationships(self) -> tuple[KnowledgeRelationship, ...]:
        """Return all relationships in deterministic order."""
        return tuple(
            self._relationships[key]
            for key in sorted(
                self._relationships,
                key=lambda item: (item[0], item[1], item[2].value),
            )
        )

    def find_for_knowledge(self, knowledge_id: str) -> tuple[KnowledgeRelationship, ...]:
        """Return relationships where the knowledge entry is source or target."""
        return tuple(
            relationship
            for relationship in self.list_relationships()
            if relationship.source_knowledge_id == knowledge_id
            or relationship.target_knowledge_id == knowledge_id
        )

    def find_by_type(
        self,
        relationship_type: KnowledgeRelationshipType,
    ) -> tuple[KnowledgeRelationship, ...]:
        """Return relationships of a given type."""
        return tuple(
            relationship
            for relationship in self.list_relationships()
            if relationship.relationship_type == relationship_type
        )
