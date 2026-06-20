"""Tests for the Configuration Snapshot Engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from configuration import DuplicateSnapshotError, SnapshotEngine, SnapshotNotFoundError
from configuration.snapshot_builder import SnapshotBuilder
from configuration.snapshot_hash import compute_snapshot_hash
from configuration.snapshot_models import ConfigurationSnapshot
from configuration.snapshot_registry import SnapshotRegistry
from configuration.snapshot_report import build_snapshot_report
from configuration.snapshot_storage import SnapshotStorage
from health.health_engine import HealthEngine
from knowledge.knowledge_engine import KnowledgeEngine
from knowledge.knowledge_pack import build_knowledge_pack
from knowledge.knowledge_registry import KnowledgeRegistry
from model import DialPeer, SipUA, VoiceService
from topology.topology_builder import TopologyBuilder

SAMPLE_PACK = {
    "id": "cisco-sip-ua-disabled",
    "title": "SIP-UA disabled operational guidance",
    "description": "Guidance when SIP-UA is administratively disabled.",
    "vendor": "cisco",
    "platform": "CUBE",
    "category": "operations",
    "severity": "critical",
    "supported_object_types": ["sip_ua"],
    "conditions": {"enabled": False},
    "recommendations": ["Enable SIP-UA and verify SIP registration."],
    "references": [],
    "version": "1.0",
}


def _provenance(**overrides: str) -> dict[str, str]:
    base = {
        "vendor": "cisco",
        "platform": "CUBE",
        "hostname": "cube-edge-01",
        "source_parser": "cisco_show_sip_ua_status",
        "source_command": "show sip-ua status",
        "source_evidence_id": "EVD-test-001",
    }
    base.update(overrides)
    return base


def _sample_topology():
    sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        allow_connections=None,
        object_id="VOBJ-voice-service-001",
    )
    dial_peer = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        destination_pattern="9T",
        object_id="VOBJ-dial-peer-001",
    )
    return TopologyBuilder().build([dial_peer, voice_service, sip_ua])


def _evaluation_outputs(topology):
    registry = KnowledgeRegistry()
    registry.register(build_knowledge_pack(SAMPLE_PACK))
    health_report = HealthEngine().evaluate_topology(topology)
    knowledge_report = KnowledgeEngine(registry).evaluate_topology(topology)
    return health_report, knowledge_report


class TestSnapshotBuilder:
    def test_builds_immutable_snapshot(self) -> None:
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        timestamp = datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)

        snapshot = SnapshotBuilder().build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-test-001",
            timestamp=timestamp,
            software_version="17.9.1",
            metadata={"source": "test"},
        )

        assert snapshot.snapshot_id == "SNAP-test-001"
        assert snapshot.timestamp == timestamp
        assert snapshot.hostname == "cube-edge-01"
        assert snapshot.vendor == "cisco"
        assert snapshot.platform == "CUBE"
        assert snapshot.software_version == "17.9.1"
        assert len(snapshot.voice_objects) == 3
        assert len(snapshot.relationships) == len(topology.relationships)
        assert snapshot.health_report.overall_score == health_report.overall_score
        assert len(snapshot.knowledge_report.matched_packs) == 1
        assert snapshot.snapshot_hash
        assert snapshot.metadata["source"] == "test"


class TestSnapshotHash:
    def test_hash_is_deterministic_for_same_content(self) -> None:
        topology = _sample_topology()
        objects = topology.all_objects()
        relationships = topology.relationships

        first = compute_snapshot_hash(objects, relationships)
        second = compute_snapshot_hash(tuple(reversed(objects)), tuple(reversed(relationships)))

        assert first == second

    def test_hash_changes_when_content_changes(self) -> None:
        topology = _sample_topology()
        changed = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
        changed_topology = TopologyBuilder().build(
            [obj for obj in topology.all_objects() if obj.id != "VOBJ-sip-ua-001"] + [changed]
        )

        original_hash = compute_snapshot_hash(topology.all_objects(), topology.relationships)
        changed_hash = compute_snapshot_hash(
            changed_topology.all_objects(),
            changed_topology.relationships,
        )

        assert original_hash != changed_hash


class TestSnapshotRegistry:
    def test_register_lookup_and_hostname_search(self) -> None:
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        builder = SnapshotBuilder()
        earlier = builder.build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-earlier",
            timestamp=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc),
        )
        later = builder.build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-later",
            timestamp=datetime(2026, 6, 20, 11, 0, tzinfo=timezone.utc),
        )

        registry = SnapshotRegistry()
        registry.register(earlier)
        registry.register(later)

        assert registry.get("SNAP-earlier") == earlier
        assert [item.snapshot_id for item in registry.lookup_by_hostname("cube-edge-01")] == [
            "SNAP-earlier",
            "SNAP-later",
        ]
        assert [item.snapshot_id for item in registry.list_snapshots()] == [
            "SNAP-earlier",
            "SNAP-later",
        ]

    def test_prevent_duplicate_snapshot_ids(self) -> None:
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        snapshot = SnapshotBuilder().build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-dup",
        )

        registry = SnapshotRegistry()
        registry.register(snapshot)

        with pytest.raises(DuplicateSnapshotError):
            registry.register(snapshot)


class TestSnapshotReport:
    def test_builds_summary_report(self) -> None:
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        snapshot = SnapshotBuilder().build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-report-001",
            timestamp=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        )

        report = build_snapshot_report(snapshot)

        assert report.snapshot_id == "SNAP-report-001"
        assert report.health_score == health_report.overall_score
        assert report.knowledge_count == 1
        assert report.snapshot_hash == snapshot.snapshot_hash
        assert report.timestamp == snapshot.timestamp
        assert report.object_counts["sip_ua"] == 1
        assert report.object_counts["voice_service"] == 1
        assert report.object_counts["dial_peer"] == 1
        assert "3 voice objects" in report.summary


class TestSnapshotEngine:
    def test_create_list_get_and_evaluate(self) -> None:
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        engine = SnapshotEngine()

        snapshot = engine.create_snapshot(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-engine-001",
            software_version="17.9.1",
        )

        assert snapshot.snapshot_id == "SNAP-engine-001"
        assert len(engine.list_snapshots()) == 1
        assert engine.get_snapshot("SNAP-engine-001") == snapshot

        report = engine.evaluate_snapshot("SNAP-engine-001")
        assert report.snapshot_id == "SNAP-engine-001"
        assert report.health_score == health_report.overall_score
        assert report.knowledge_count == 1

    def test_get_snapshot_raises_when_missing(self) -> None:
        engine = SnapshotEngine()

        with pytest.raises(SnapshotNotFoundError):
            engine.get_snapshot("SNAP-missing")

    def test_storage_is_in_memory_only(self) -> None:
        storage = SnapshotStorage()
        topology = _sample_topology()
        health_report, knowledge_report = _evaluation_outputs(topology)
        snapshot = SnapshotBuilder().build(
            topology,
            health_report,
            knowledge_report,
            snapshot_id="SNAP-storage-001",
        )

        storage.store(snapshot)

        assert storage.get("SNAP-storage-001") == snapshot
        assert storage.list_snapshots() == (snapshot,)
