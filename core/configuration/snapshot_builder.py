"""Build immutable configuration snapshots from evaluation outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from configuration.snapshot_hash import compute_snapshot_hash
from configuration.snapshot_models import ConfigurationSnapshot
from health.health_report import HealthReport
from knowledge.knowledge_report import KnowledgeReport
from model.voice_topology import VoiceTopology
from shared.constants import ID_PREFIX_SNAPSHOT
from shared.types import JsonDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SnapshotBuilder:
    """Create immutable snapshots from topology and evaluation reports."""

    def build(
        self,
        topology: VoiceTopology,
        health_report: HealthReport,
        knowledge_report: KnowledgeReport,
        *,
        snapshot_id: str | None = None,
        timestamp: datetime | None = None,
        software_version: str | None = None,
        metadata: JsonDict | None = None,
    ) -> ConfigurationSnapshot:
        """Build a content-addressed configuration snapshot."""
        voice_objects = tuple(sorted(topology.all_objects(), key=lambda item: item.id))
        relationships = tuple(
            sorted(topology.relationships, key=lambda item: item.relationship_id)
        )
        scope = _derive_scope(voice_objects, metadata or {})
        resolved_metadata = dict(metadata or {})
        resolved_software_version = software_version or resolved_metadata.get(
            "software_version", "unknown"
        )

        snapshot_hash = compute_snapshot_hash(voice_objects, relationships)
        return ConfigurationSnapshot(
            snapshot_id=snapshot_id or _new_snapshot_id(),
            timestamp=timestamp or _utc_now(),
            hostname=scope["hostname"],
            vendor=scope["vendor"],
            platform=scope["platform"],
            software_version=str(resolved_software_version),
            voice_objects=voice_objects,
            relationships=relationships,
            health_report=health_report,
            knowledge_report=knowledge_report,
            metadata=resolved_metadata,
            snapshot_hash=snapshot_hash,
        )


def _new_snapshot_id() -> str:
    return f"{ID_PREFIX_SNAPSHOT}{uuid4().hex[:12]}"


def _derive_scope(voice_objects, metadata: JsonDict) -> dict[str, str]:
    if not voice_objects:
        return {
            "hostname": str(metadata.get("hostname", "unknown")),
            "vendor": str(metadata.get("vendor", "unknown")),
            "platform": str(metadata.get("platform", "unknown")),
        }

    hostname = voice_objects[0].hostname
    vendor = voice_objects[0].vendor
    platform = voice_objects[0].platform
    return {
        "hostname": hostname,
        "vendor": vendor,
        "platform": platform,
    }
