"""In-memory snapshot storage for Sprint 8.1."""

from __future__ import annotations

from configuration.snapshot_models import ConfigurationSnapshot
from configuration.snapshot_registry import SnapshotRegistry


class SnapshotStorage:
    """Store configuration snapshots in memory only."""

    def __init__(self, registry: SnapshotRegistry | None = None) -> None:
        self._registry = registry or SnapshotRegistry()

    @property
    def registry(self) -> SnapshotRegistry:
        """Return the backing registry."""
        return self._registry

    def store(self, snapshot: ConfigurationSnapshot) -> None:
        """Persist one snapshot in memory."""
        self._registry.register(snapshot)

    def get(self, snapshot_id: str) -> ConfigurationSnapshot | None:
        """Return one snapshot by identifier."""
        return self._registry.get(snapshot_id)

    def lookup_by_hostname(self, hostname: str) -> tuple[ConfigurationSnapshot, ...]:
        """Return snapshots for a hostname ordered by timestamp."""
        return self._registry.lookup_by_hostname(hostname)

    def list_snapshots(self) -> tuple[ConfigurationSnapshot, ...]:
        """Return all stored snapshots ordered by timestamp."""
        return self._registry.list_snapshots()
