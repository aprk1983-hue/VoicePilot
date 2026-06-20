"""Configuration snapshot engine."""

from __future__ import annotations

from configuration.snapshot_builder import SnapshotBuilder
from configuration.snapshot_exceptions import SnapshotNotFoundError
from configuration.snapshot_models import ConfigurationSnapshot
from configuration.snapshot_report import SnapshotReport, build_snapshot_report
from configuration.snapshot_storage import SnapshotStorage
from health.health_report import HealthReport
from knowledge.knowledge_report import KnowledgeReport
from model.voice_topology import VoiceTopology
from shared.types import JsonDict


class SnapshotEngine:
    """Create, store, and evaluate configuration snapshots."""

    def __init__(
        self,
        storage: SnapshotStorage | None = None,
        builder: SnapshotBuilder | None = None,
    ) -> None:
        self._storage = storage or SnapshotStorage()
        self._builder = builder or SnapshotBuilder()

    @property
    def storage(self) -> SnapshotStorage:
        """Return the snapshot storage backend."""
        return self._storage

    def create_snapshot(
        self,
        topology: VoiceTopology,
        health_report: HealthReport,
        knowledge_report: KnowledgeReport,
        *,
        snapshot_id: str | None = None,
        software_version: str | None = None,
        metadata: JsonDict | None = None,
    ) -> ConfigurationSnapshot:
        """Build and store an immutable configuration snapshot."""
        snapshot = self._builder.build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id=snapshot_id,
            software_version=software_version,
            metadata=metadata,
        )
        self._storage.store(snapshot)
        return snapshot

    def list_snapshots(self) -> tuple[ConfigurationSnapshot, ...]:
        """Return stored snapshots ordered by timestamp."""
        return self._storage.list_snapshots()

    def get_snapshot(self, snapshot_id: str) -> ConfigurationSnapshot:
        """Return one snapshot by identifier."""
        snapshot = self._storage.get(snapshot_id)
        if snapshot is None:
            raise SnapshotNotFoundError(snapshot_id)
        return snapshot

    def evaluate_snapshot(self, snapshot_id: str) -> SnapshotReport:
        """Return a summary report for one snapshot."""
        snapshot = self.get_snapshot(snapshot_id)
        return build_snapshot_report(snapshot)
