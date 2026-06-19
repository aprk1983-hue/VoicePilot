"""Registry for canonical voice objects."""

from __future__ import annotations

from model.voice_graph import VoiceObject


class ObjectRegistryError(RuntimeError):
    """Raised when registry invariants are violated."""


class ObjectRegistry:
    """Append-only registry for immutable voice objects.

    Lookup by ID, object type, hostname, or source parser.
    Objects are never overwritten after registration.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, VoiceObject] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_hostname: dict[str, list[str]] = {}
        self._by_parser: dict[str, list[str]] = {}
        self._order: list[str] = []

    def register(self, obj: VoiceObject) -> VoiceObject:
        """Register an object. Raises if the ID already exists."""
        if obj.id in self._by_id:
            raise ObjectRegistryError(
                f"Voice object {obj.id} is already registered; registry is append-only."
            )

        self._by_id[obj.id] = obj
        self._order.append(obj.id)
        self._index(self._by_type, obj.object_type, obj.id)
        self._index(self._by_hostname, obj.hostname, obj.id)
        self._index(self._by_parser, obj.source_parser, obj.id)
        return obj

    def get_by_id(self, object_id: str) -> VoiceObject | None:
        return self._by_id.get(object_id)

    def require_by_id(self, object_id: str) -> VoiceObject:
        obj = self.get_by_id(object_id)
        if obj is None:
            raise ObjectRegistryError(f"Voice object not found: {object_id}")
        return obj

    def list_by_type(self, object_type: str) -> list[VoiceObject]:
        return self._resolve(self._by_type.get(object_type, []))

    def list_by_hostname(self, hostname: str) -> list[VoiceObject]:
        return self._resolve(self._by_hostname.get(hostname, []))

    def list_by_parser(self, source_parser: str) -> list[VoiceObject]:
        return self._resolve(self._by_parser.get(source_parser, []))

    def list_all(self) -> list[VoiceObject]:
        return [self._by_id[object_id] for object_id in self._order]

    def __len__(self) -> int:
        return len(self._order)

    def _resolve(self, object_ids: list[str]) -> list[VoiceObject]:
        return [self._by_id[object_id] for object_id in object_ids]

    @staticmethod
    def _index(index: dict[str, list[str]], key: str, object_id: str) -> None:
        index.setdefault(key, []).append(object_id)
