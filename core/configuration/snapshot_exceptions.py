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


class DuplicateBaselineError(SnapshotError):
    """Raised when registering a baseline with an existing identifier."""

    def __init__(self, baseline_id: str) -> None:
        super().__init__(f"Baseline already registered: {baseline_id}")
        self.baseline_id = baseline_id


class BaselineNotFoundError(SnapshotError):
    """Raised when a baseline cannot be resolved."""

    def __init__(self, baseline_id: str | None = None, *, hostname: str | None = None) -> None:
        if hostname:
            super().__init__(f"No baseline found for hostname: {hostname}")
            self.hostname = hostname
            self.baseline_id = None
        else:
            super().__init__(f"Baseline not found: {baseline_id}")
            self.baseline_id = baseline_id
            self.hostname = None
