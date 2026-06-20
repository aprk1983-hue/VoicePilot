"""Registry for structured knowledge packs."""

from __future__ import annotations

from knowledge.knowledge_exceptions import DuplicateKnowledgePackError
from knowledge.knowledge_models import KnowledgePack


class KnowledgeRegistry:
    """Register and lookup knowledge packs."""

    def __init__(self) -> None:
        self._packs: dict[str, KnowledgePack] = {}

    def register(self, pack: KnowledgePack) -> None:
        """Register a knowledge pack, preventing duplicate identifiers."""
        if pack.id in self._packs:
            raise DuplicateKnowledgePackError(pack.id)
        self._packs[pack.id] = pack

    def get(self, pack_id: str) -> KnowledgePack | None:
        """Return a pack by identifier."""
        return self._packs.get(pack_id)

    def search_by_object_type(self, object_type: str) -> tuple[KnowledgePack, ...]:
        """Return packs applicable to an object type in deterministic order."""
        return tuple(
            sorted(
                (
                    pack
                    for pack in self._packs.values()
                    if object_type in pack.supported_object_types
                ),
                key=lambda item: item.id,
            )
        )

    def all_packs(self) -> tuple[KnowledgePack, ...]:
        """Return all registered packs in deterministic order."""
        return tuple(sorted(self._packs.values(), key=lambda item: item.id))
