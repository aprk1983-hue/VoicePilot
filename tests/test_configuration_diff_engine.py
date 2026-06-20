"""Tests for the Configuration Diff Engine."""

from __future__ import annotations

from datetime import datetime, timezone

from configuration.diff_engine import DiffEngine, comparable_object_dict
from configuration.diff_models import DiffChangeType, DiffRiskLevel
from configuration.diff_report import format_diff_report_markdown
from configuration.snapshot_builder import SnapshotBuilder
from health.health_engine import HealthEngine
from knowledge.knowledge_report import KnowledgeReport
from model import DialPeer, Provider, SipUA, VoiceService
from topology.topology_builder import TopologyBuilder


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


def _empty_knowledge_report() -> KnowledgeReport:
    return KnowledgeReport()


def _snapshot(
    snapshot_id: str,
    objects: list,
    *,
    timestamp: datetime | None = None,
) -> object:
    topology = TopologyBuilder().build(objects)
    health_report = HealthEngine().evaluate_topology(topology)
    return SnapshotBuilder().build(
        topology,
        health_report,
        _empty_knowledge_report(),
        snapshot_id=snapshot_id,
        timestamp=timestamp or datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        software_version="17.9.1",
    )


class TestConfigurationDiffEngine:
    def test_detects_added_object(self) -> None:
        base = [
            SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001"),
        ]
        extended = base + [
            Provider.create(
                **_provenance(),
                name="ITSP-Primary",
                addresses=("ipv4:192.0.2.10",),
                object_id="VOBJ-provider-001",
            )
        ]

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", base),
            _snapshot("SNAP-002", extended),
        )

        assert len(diff.added) == 1
        assert diff.added[0].change_type == DiffChangeType.ADDED
        assert diff.added[0].severity == DiffRiskLevel.LOW.value

    def test_detects_removed_provider_as_high_risk(self) -> None:
        before_objects = [
            Provider.create(
                **_provenance(),
                name="ITSP-Primary",
                addresses=("ipv4:192.0.2.10",),
                object_id="VOBJ-provider-001",
            )
        ]
        after_objects: list = []

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", before_objects),
            _snapshot("SNAP-002", after_objects),
        )

        assert len(diff.removed) == 1
        assert diff.removed[0].change_type == DiffChangeType.REMOVED
        assert diff.removed[0].severity == DiffRiskLevel.HIGH.value
        assert "Provider ITSP-Primary removed" in diff.removed[0].summary

    def test_detects_modified_sip_ua_enabled_true_to_false(self) -> None:
        before = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
        after = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", [before]),
            _snapshot("SNAP-002", [after]),
        )

        assert len(diff.modified) == 1
        assert diff.modified[0].change_type == DiffChangeType.MODIFIED
        assert "enabled" in diff.modified[0].changed_fields
        assert diff.modified[0].severity == DiffRiskLevel.CRITICAL.value
        assert diff.risk_level == DiffRiskLevel.CRITICAL.value

    def test_detects_modified_dial_peer_destination_pattern(self) -> None:
        before = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=100,
            destination_pattern="9T",
            object_id="VOBJ-dial-peer-100",
        )
        after = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=100,
            destination_pattern="8T",
            object_id="VOBJ-dial-peer-100",
        )

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", [before]),
            _snapshot("SNAP-002", [after]),
        )

        assert len(diff.modified) == 1
        assert diff.modified[0].severity == DiffRiskLevel.MEDIUM.value
        assert "destination_pattern" in diff.modified[0].changed_fields

    def test_ignores_provenance_only_fields(self) -> None:
        before = SipUA.create(
            **_provenance(source_parser="parser_a", source_evidence_id="EVD-a"),
            enabled=True,
            object_id="VOBJ-sip-ua-001",
        )
        after = SipUA.create(
            **_provenance(source_parser="parser_b", source_evidence_id="EVD-b"),
            enabled=True,
            object_id="VOBJ-sip-ua-001",
        )

        engine = DiffEngine()
        object_diff = engine.compare_objects(before, after)
        diff = engine.compare(
            _snapshot("SNAP-001", [before]),
            _snapshot("SNAP-002", [after]),
        )

        assert object_diff.change_type == DiffChangeType.UNCHANGED
        assert "source_parser" not in comparable_object_dict(before)
        assert diff.unchanged_count == 1
        assert diff.modified == ()

    def test_reports_unchanged_count(self) -> None:
        objects = [
            SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001"),
            VoiceService.create(
                **_provenance(
                    source_parser="cisco_show_run_voice_service_voip",
                    source_command="show run | sec voice service voip",
                ),
                allow_connections=True,
                object_id="VOBJ-voice-service-001",
            ),
        ]

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", objects),
            _snapshot("SNAP-002", objects),
        )

        assert diff.unchanged_count == 2
        assert diff.added == ()
        assert diff.removed == ()
        assert diff.modified == ()
        assert diff.risk_level == DiffRiskLevel.NONE.value

    def test_summarize_and_markdown_report(self) -> None:
        before = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
        after = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        shutdown_before = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=100,
            shutdown=False,
            object_id="VOBJ-dial-peer-100",
        )
        shutdown_after = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=100,
            shutdown=True,
            object_id="VOBJ-dial-peer-100",
        )

        engine = DiffEngine()
        diff = engine.compare(
            _snapshot("SNAP-001", [before, shutdown_before]),
            _snapshot("SNAP-002", [after, shutdown_after]),
        )
        summary = engine.summarize(diff)
        markdown = format_diff_report_markdown(diff)

        assert "SNAP-001" in summary
        assert "SNAP-002" in summary
        assert diff.risk_level == DiffRiskLevel.CRITICAL.value
        assert "## Configuration Diff" in markdown
        assert "Before: SNAP-001" in markdown
        assert "After: SNAP-002" in markdown
        assert "CRITICAL:" in markdown
        assert "SipUA changed from enabled to disabled" in markdown
        assert "HIGH:" in markdown
        assert "DialPeer dial-peer 100 changed to shutdown" in markdown

    def test_voice_service_allow_connections_risk(self) -> None:
        before = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=True,
            object_id="VOBJ-voice-service-001",
        )
        after = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=None,
            object_id="VOBJ-voice-service-001",
        )

        diff = DiffEngine().compare(
            _snapshot("SNAP-001", [before]),
            _snapshot("SNAP-002", [after]),
        )

        assert diff.modified[0].severity == DiffRiskLevel.HIGH.value
        assert diff.risk_level == DiffRiskLevel.HIGH.value
