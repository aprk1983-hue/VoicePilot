"""Engineering Knowledge Framework exceptions."""

from __future__ import annotations


class EngineeringKnowledgeError(Exception):
    """Base exception for the Engineering Knowledge Framework."""


class DuplicateEngineeringKnowledgeError(EngineeringKnowledgeError):
    """Raised when registering knowledge with an existing ID."""

    def __init__(self, knowledge_id: str) -> None:
        super().__init__(f"Engineering knowledge already registered: {knowledge_id}")
        self.knowledge_id = knowledge_id


class EngineeringKnowledgeNotFoundError(EngineeringKnowledgeError):
    """Raised when a knowledge ID is not registered."""

    def __init__(self, knowledge_id: str) -> None:
        super().__init__(f"Engineering knowledge not found: {knowledge_id}")
        self.knowledge_id = knowledge_id


class DuplicateKnowledgeRelationshipError(EngineeringKnowledgeError):
    """Raised when registering a duplicate knowledge relationship."""

    def __init__(self, source_knowledge_id: str, target_knowledge_id: str, relationship_type: str) -> None:
        super().__init__(
            "Knowledge relationship already registered: "
            f"{source_knowledge_id} -> {target_knowledge_id} ({relationship_type})"
        )


class KnowledgeRelationshipNotFoundError(EngineeringKnowledgeError):
    """Raised when a knowledge relationship cannot be found."""

    def __init__(self, source_knowledge_id: str, target_knowledge_id: str, relationship_type: str) -> None:
        super().__init__(
            f"Knowledge relationship not found: "
            f"{source_knowledge_id} -> {target_knowledge_id} ({relationship_type})"
        )


class KnowledgeGraphNodeNotFoundError(EngineeringKnowledgeError):
    """Raised when a graph node cannot be resolved."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"Knowledge graph node not found: {node_id}")
        self.node_id = node_id
