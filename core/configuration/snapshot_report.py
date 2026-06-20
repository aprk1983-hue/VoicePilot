"""Snapshot evaluation report."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from configuration.snapshot_models import ConfigurationSnapshot
from shared.types import JsonDict


@dataclass(frozen=True)
class SnapshotReport:
    """Human-readable summary of one configuration snapshot."""

    snapshot_id: str
    summary: str
    object_counts: JsonDict
    health_score: int
    knowledge_count: int
    snapshot_hash: str
    timestamp: datetime
    hostname: str
    vendor: str
    platform: str
    software_version: str
    metadata: JsonDict = field(default_factory=dict)


def build_snapshot_report(snapshot: ConfigurationSnapshot) -> SnapshotReport:
    """Build a report summary for one snapshot."""
    object_counts = _count_objects(snapshot)
    knowledge_count = len(snapshot.knowledge_report.matched_packs)
    summary = (
        f"Snapshot {snapshot.snapshot_id} captured {sum(object_counts.values())} "
        f"voice objects with health score {snapshot.health_report.overall_score}/100 "
        f"and {knowledge_count} matched knowledge packs."
    )
    return SnapshotReport(
        snapshot_id=snapshot.snapshot_id,
        summary=summary,
        object_counts=object_counts,
        health_score=snapshot.health_report.overall_score,
        knowledge_count=knowledge_count,
        snapshot_hash=snapshot.snapshot_hash,
        timestamp=snapshot.timestamp,
        hostname=snapshot.hostname,
        vendor=snapshot.vendor,
        platform=snapshot.platform,
        software_version=snapshot.software_version,
        metadata=dict(snapshot.metadata),
    )


def _count_objects(snapshot: ConfigurationSnapshot) -> dict[str, int]:
    counts: dict[str, int] = {}
    for obj in snapshot.voice_objects:
        counts[obj.object_type] = counts.get(obj.object_type, 0) + 1
    return dict(sorted(counts.items()))
