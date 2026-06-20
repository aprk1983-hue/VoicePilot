"""Exceptions raised by the Voice Knowledge Framework."""


class KnowledgeSchemaError(Exception):
    """Raised when a knowledge pack fails schema validation."""


class KnowledgeLoadError(Exception):
    """Raised when a knowledge pack cannot be loaded."""


class DuplicateKnowledgePackError(Exception):
    """Raised when registering a pack with an existing identifier."""

    def __init__(self, pack_id: str) -> None:
        self.pack_id = pack_id
        super().__init__(f"Knowledge pack already registered: {pack_id}")
