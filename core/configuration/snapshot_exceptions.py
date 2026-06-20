"""Configuration snapshot exceptions."""

from __future__ import annotations


class SnapshotError(Exception):
    """Base error for configuration snapshot operations."""


class DuplicateSnapshotError(SnapshotError):
    """Raised when registering a snapshot with an existing identifier."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(f"Snapshot already registered: {snapshot_id}")
        self.snapshot_id = snapshot_id


class SnapshotNotFoundError(SnapshotError):
    """Raised when a snapshot identifier cannot be resolved."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(f"Snapshot not found: {snapshot_id}")
        self.snapshot_id = snapshot_id
