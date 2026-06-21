"""In-memory engineering knowledge registry."""

from __future__ import annotations

from engineering_knowledge.knowledge_exceptions import (
    DuplicateEngineeringKnowledgeError,
    EngineeringKnowledgeNotFoundError,
)
from engineering_knowledge.knowledge_models import EngineeringKnowledge


class EngineeringKnowledgeRegistry:
    """Store and retrieve engineering knowledge entries in memory."""

    def __init__(self) -> None:
        self._entries: dict[str, EngineeringKnowledge] = {}

    def register(self, knowledge: EngineeringKnowledge) -> EngineeringKnowledge:
        """Register knowledge, preventing duplicate IDs."""
        if knowledge.knowledge_id in self._entries:
            raise DuplicateEngineeringKnowledgeError(knowledge.knowledge_id)
        self._entries[knowledge.knowledge_id] = knowledge
        return knowledge

    def remove(self, knowledge_id: str) -> None:
        """Remove knowledge from the registry."""
        if knowledge_id not in self._entries:
            raise EngineeringKnowledgeNotFoundError(knowledge_id)
        del self._entries[knowledge_id]

    def get(self, knowledge_id: str) -> EngineeringKnowledge:
        """Return knowledge by ID."""
        entry = self._entries.get(knowledge_id)
        if entry is None:
            raise EngineeringKnowledgeNotFoundError(knowledge_id)
        return entry

    def exists(self, knowledge_id: str) -> bool:
        """Return whether a knowledge ID is registered."""
        return knowledge_id in self._entries

    def list_knowledge(self) -> tuple[EngineeringKnowledge, ...]:
        """Return all knowledge entries in deterministic order."""
        return tuple(self._entries[knowledge_id] for knowledge_id in sorted(self._entries))
