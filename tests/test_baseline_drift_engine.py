"""Tests for baseline and drift engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from configuration.baseline_models import DriftStatus
from configuration.baseline_registry import BaselineRegistry
from configuration.diff_models import DiffRiskLevel
from configuration.drift_engine import DriftEngine
from configuration.drift_report import format_drift_report_markdown
from configuration.snapshot_builder import SnapshotBuilder
from configuration.snapshot_exceptions import BaselineNotFoundError, DuplicateBaselineError
from health.health_engine import HealthEngine
from knowledge.knowledge_report import KnowledgeReport
from model import DialPeer, Provider, SipUA
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


class TestBaselineRegistry:
    def test_register_baseline(self) -> None:
        registry = BaselineRegistry()
        snapshot = _snapshot(
            "SNAP-base-001",
            [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")],
        )

        baseline = registry.register_baseline(
            snapshot,
            approved_by="ops-lead",
            label="Approved CUBE baseline",
            description="Post-change validation",
            baseline_id="BASE-test-001",
            approved_at=datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc),
        )

        assert baseline.baseline_id == "BASE-test-001"
        assert baseline.snapshot_id == "SNAP-base-001"
        assert baseline.hostname == "cube-edge-01"
        assert baseline.approved_by == "ops-lead"
        assert baseline.label == "Approved CUBE baseline"
        assert registry.get_snapshot("SNAP-base-001") == snapshot

    def test_get_latest_baseline(self) -> None:
        registry = BaselineRegistry()
        objects = [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")]
        earlier_snapshot = _snapshot("SNAP-base-001", objects)
        later_snapshot = _snapshot("SNAP-base-002", objects)

        registry.register_baseline(
            earlier_snapshot,
            approved_by="ops-lead",
            label="Earlier baseline",
            baseline_id="BASE-earlier",
            approved_at=datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc),
        )
        registry.register_baseline(
            later_snapshot,
            approved_by="ops-lead",
            label="Latest baseline",
            baseline_id="BASE-latest",
            approved_at=datetime(2026, 6, 20, 11, 0, tzinfo=timezone.utc),
        )

        latest = registry.get_latest_baseline("cube-edge-01")

        assert latest is not None
        assert latest.baseline_id == "BASE-latest"
        assert [item.baseline_id for item in registry.list_baselines("cube-edge-01")] == [
            "BASE-earlier",
            "BASE-latest",
        ]

    def test_prevent_duplicate_baseline_ids(self) -> None:
        registry = BaselineRegistry()
        snapshot = _snapshot(
            "SNAP-base-001",
            [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")],
        )
        registry.register_baseline(
            snapshot,
            approved_by="ops-lead",
            label="Baseline",
            baseline_id="BASE-dup",
        )

        with pytest.raises(DuplicateBaselineError):
            registry.register_baseline(
                snapshot,
                approved_by="ops-lead",
                label="Duplicate",
                baseline_id="BASE-dup",
            )


class TestDriftEngine:
    def _engine_with_baseline(self, baseline_objects, baseline_id="BASE-approved"):
        registry = BaselineRegistry()
        baseline_snapshot = _snapshot("SNAP-base-001", baseline_objects)
        baseline = registry.register_baseline(
            baseline_snapshot,
            approved_by="ops-lead",
            label="Approved baseline",
            baseline_id=baseline_id,
        )
        return DriftEngine(baseline_registry=registry), baseline

    def test_no_drift(self) -> None:
        objects = [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")]
        engine, baseline = self._engine_with_baseline(objects)
        current = _snapshot("SNAP-current-001", objects)

        report = engine.compare_to_baseline(current, baseline)

        assert report.drift_status == DriftStatus.NO_DRIFT
        assert report.recommendations == ("No action required.",)
        assert report.diff.risk_level == DiffRiskLevel.NONE.value

    def test_low_drift_added_object(self) -> None:
        base = [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")]
        current_objects = base + [
            Provider.create(
                **_provenance(),
                name="ITSP-Primary",
                addresses=("ipv4:192.0.2.10",),
                object_id="VOBJ-provider-001",
            )
        ]
        engine, baseline = self._engine_with_baseline(base)
        current = _snapshot("SNAP-current-001", current_objects)

        report = engine.compare_to_latest_baseline(current, "cube-edge-01")

        assert report.drift_status == DriftStatus.LOW_DRIFT
        assert report.recommendations == ("Document change if expected.",)
        assert len(report.diff.added) == 1

    def test_critical_drift_sip_ua_disabled(self) -> None:
        before = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
        after = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        engine, baseline = self._engine_with_baseline([before])
        current = _snapshot("SNAP-current-001", [after])

        report = engine.compare_to_baseline(current, baseline)

        assert report.drift_status == DriftStatus.CRITICAL_DRIFT
        assert report.recommendations == ("Review immediately before production impact.",)
        assert report.diff.risk_level == DiffRiskLevel.CRITICAL.value

    def test_high_drift_dial_peer_shutdown(self) -> None:
        before = [
            SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001"),
            DialPeer.create(
                **_provenance(
                    source_parser="cisco_show_dial_peer_voice_summary",
                    source_command="show dial-peer voice summary",
                ),
                tag=100,
                shutdown=False,
                object_id="VOBJ-dial-peer-100",
            ),
        ]
        after = [
            SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001"),
            DialPeer.create(
                **_provenance(
                    source_parser="cisco_show_dial_peer_voice_summary",
                    source_command="show dial-peer voice summary",
                ),
                tag=100,
                shutdown=True,
                object_id="VOBJ-dial-peer-100",
            ),
        ]
        engine, baseline = self._engine_with_baseline(before)
        current = _snapshot("SNAP-current-001", after)

        report = engine.compare_to_baseline(current, baseline)

        assert report.drift_status == DriftStatus.HIGH_DRIFT
        assert report.recommendations == (
            "Validate changes against approved change record.",
        )

    def test_compare_to_latest_baseline_raises_when_missing(self) -> None:
        engine = DriftEngine()
        current = _snapshot(
            "SNAP-current-001",
            [SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")],
        )

        with pytest.raises(BaselineNotFoundError):
            engine.compare_to_latest_baseline(current, "cube-edge-01")

    def test_drift_report_markdown(self) -> None:
        before = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
        after = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        engine, baseline = self._engine_with_baseline([before])
        current = _snapshot("SNAP-current-001", [after])

        report = engine.compare_to_baseline(current, baseline)
        markdown = format_drift_report_markdown(report)

        assert "## Baseline Drift Report" in markdown
        assert "BASE-approved" in markdown
        assert "Drift Status: CRITICAL_DRIFT" in markdown
        assert "Review immediately before production impact." in markdown
        assert "## Configuration Diff" in markdown
        assert "SipUA changed from enabled to disabled" in markdown
