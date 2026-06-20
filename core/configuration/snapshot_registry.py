"""In-memory snapshot registry."""

from __future__ import annotations

from configuration.snapshot_exceptions import DuplicateSnapshotError
from configuration.snapshot_models import ConfigurationSnapshot


class SnapshotRegistry:
    """Register and lookup configuration snapshots."""

    def __init__(self) -> None:
        self._snapshots: dict[str, ConfigurationSnapshot] = {}

    def register(self, snapshot: ConfigurationSnapshot) -> None:
        """Register a snapshot, preventing duplicate identifiers."""
        if snapshot.snapshot_id in self._snapshots:
            raise DuplicateSnapshotError(snapshot.snapshot_id)
        self._snapshots[snapshot.snapshot_id] = snapshot

    def get(self, snapshot_id: str) -> ConfigurationSnapshot | None:
        """Return a snapshot by identifier."""
        return self._snapshots.get(snapshot_id)

    def lookup_by_hostname(self, hostname: str) -> tuple[ConfigurationSnapshot, ...]:
        """Return snapshots for a hostname ordered by timestamp."""
        normalized = hostname.strip().lower()
        matches = [
            snapshot
            for snapshot in self._snapshots.values()
            if snapshot.hostname.strip().lower() == normalized
        ]
        return tuple(sorted(matches, key=lambda item: (item.timestamp, item.snapshot_id)))

    def list_snapshots(self) -> tuple[ConfigurationSnapshot, ...]:
        """Return all snapshots ordered by timestamp."""
        return tuple(
            sorted(
                self._snapshots.values(),
                key=lambda item: (item.timestamp, item.snapshot_id),
            )
        )
