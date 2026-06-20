"""Tests for deterministic voice topology impact analysis."""

from __future__ import annotations

import pytest

from model import DialPeer, Interface, Provider, SipUA, VoiceService, VoiceTopology
from topology.impact_engine import ImpactEngine
from topology.impact_models import ImpactSeverity
from topology.relationship_types import RelationshipType
from topology.topology_builder import TopologyBuilder
from topology.topology_exceptions import TopologyObjectNotFoundError


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


def _full_chain_topology() -> VoiceTopology:
    sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        object_id="VOBJ-voice-service-001",
    )
    dial_peer = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        session_target="ipv4:192.0.2.10",
        object_id="VOBJ-dial-peer-001",
    )
    interface = Interface.create(
        **_provenance(
            source_parser="cisco_show_version",
            source_command="show version",
        ),
        name="GigabitEthernet0/0",
        object_id="VOBJ-interface-001",
    )
    provider = Provider.create(
        **_provenance(),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-001",
    )
    return TopologyBuilder().build([dial_peer, voice_service, sip_ua, interface, provider])


def _topology_with_dial_peer_count(count: int) -> tuple[VoiceTopology, SipUA, VoiceService, tuple[DialPeer, ...]]:
    sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-root")
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        object_id="VOBJ-voice-service-root",
    )
    dial_peers = tuple(
        DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=index + 1,
            object_id=f"VOBJ-dial-peer-{index + 1:03d}",
        )
        for index in range(count)
    )
    topology = TopologyBuilder().build([*dial_peers, voice_service, sip_ua])
    return topology, sip_ua, voice_service, dial_peers


class TestImpactEngine:
    def test_sip_ua_impact(self) -> None:
        topology = _full_chain_topology()
        report = ImpactEngine().analyze_failure(topology, "VOBJ-sip-ua-001")

        assert report.affected_object.id == "VOBJ-sip-ua-001"
        assert report.severity == ImpactSeverity.MEDIUM
        assert [obj.id for obj in report.impacted_objects] == [
            "VOBJ-dial-peer-001",
            "VOBJ-voice-service-001",
        ]
        assert "Failure of sip-ua (sip_ua)" in report.summary
        assert report.recommendations == ("Validate SIP registration after change.",)

    def test_voice_service_impact(self) -> None:
        topology = _full_chain_topology()
        report = ImpactEngine().analyze_removal(topology, "VOBJ-voice-service-001")

        assert report.severity == ImpactSeverity.MEDIUM
        assert [obj.id for obj in report.impacted_objects] == ["VOBJ-dial-peer-001"]
        assert "Removal of voice-service (voice_service)" in report.summary
        assert report.recommendations == ("Verify all outbound dial peers.",)

    def test_dial_peer_impact(self) -> None:
        topology = _full_chain_topology()
        report = ImpactEngine().analyze_configuration_change(topology, "VOBJ-dial-peer-001")

        assert report.severity == ImpactSeverity.LOW
        assert report.impacted_objects == ()
        assert "has no graph-derived dependents" in report.summary
        assert report.recommendations == ("Perform outbound PSTN test.",)

    def test_provider_impact(self) -> None:
        topology = _full_chain_topology()
        report = ImpactEngine().analyze_failure(topology, "VOBJ-provider-001")

        assert report.severity == ImpactSeverity.MEDIUM
        assert [obj.id for obj in report.impacted_objects] == ["VOBJ-dial-peer-001"]
        assert report.recommendations == ("Verify all associated trunks.",)

    def test_no_dependents_is_low_severity(self) -> None:
        interface = Interface.create(
            **_provenance(
                source_parser="cisco_show_version",
                source_command="show version",
            ),
            name="GigabitEthernet0/0",
            object_id="VOBJ-interface-isolated",
        )
        topology = TopologyBuilder().build([interface])
        report = ImpactEngine().analyze_failure(topology, "VOBJ-interface-isolated")

        assert report.severity == ImpactSeverity.LOW
        assert report.impacted_objects == ()
        assert report.dependency_paths == ()
        assert report.recommendations == ()

    @pytest.mark.parametrize(
        ("dial_peer_count", "expected_severity"),
        (
            (0, ImpactSeverity.MEDIUM),
            (1, ImpactSeverity.MEDIUM),
            (2, ImpactSeverity.HIGH),
            (3, ImpactSeverity.HIGH),
            (5, ImpactSeverity.CRITICAL),
            (6, ImpactSeverity.CRITICAL),
        ),
    )
    def test_severity_thresholds(
        self,
        dial_peer_count: int,
        expected_severity: ImpactSeverity,
    ) -> None:
        topology, sip_ua, _, _ = _topology_with_dial_peer_count(dial_peer_count)
        report = ImpactEngine().analyze_failure(topology, sip_ua.id)

        assert len(report.impacted_objects) == dial_peer_count + 1
        assert report.severity == expected_severity

    def test_recommendation_generation_by_object_type(self) -> None:
        topology = _full_chain_topology()
        engine = ImpactEngine()

        assert engine.analyze_failure(topology, "VOBJ-sip-ua-001").recommendations[0].startswith(
            "Validate SIP registration"
        )
        assert engine.analyze_failure(topology, "VOBJ-voice-service-001").recommendations[0].startswith(
            "Verify all outbound dial peers"
        )
        assert engine.analyze_failure(topology, "VOBJ-dial-peer-001").recommendations[0].startswith(
            "Perform outbound PSTN test"
        )
        assert engine.analyze_failure(topology, "VOBJ-provider-001").recommendations[0].startswith(
            "Verify all associated trunks"
        )

    def test_dependency_path_generation(self) -> None:
        topology = _full_chain_topology()
        report = ImpactEngine().analyze_failure(topology, "VOBJ-sip-ua-001")

        paths_by_id = {path.impacted_object_id: path for path in report.dependency_paths}
        dial_peer_path = paths_by_id["VOBJ-dial-peer-001"]
        voice_service_path = paths_by_id["VOBJ-voice-service-001"]

        assert len(dial_peer_path.relationships) == 2
        assert dial_peer_path.relationships[0].relationship_type == RelationshipType.USES.value
        assert dial_peer_path.relationships[0].source_object_id == "VOBJ-dial-peer-001"
        assert dial_peer_path.relationships[0].target_object_id == "VOBJ-voice-service-001"
        assert dial_peer_path.relationships[1].source_object_id == "VOBJ-voice-service-001"
        assert dial_peer_path.relationships[1].target_object_id == "VOBJ-sip-ua-001"
        assert len(voice_service_path.relationships) == 1
        assert voice_service_path.relationships[0].target_object_id == "VOBJ-sip-ua-001"

    def test_missing_object_raises_typed_error(self) -> None:
        topology = _full_chain_topology()

        with pytest.raises(TopologyObjectNotFoundError):
            ImpactEngine().analyze_failure(topology, "VOBJ-missing")

    def test_analyze_methods_differ_only_in_summary(self) -> None:
        topology = _full_chain_topology()
        engine = ImpactEngine()

        failure = engine.analyze_failure(topology, "VOBJ-sip-ua-001")
        removal = engine.analyze_removal(topology, "VOBJ-sip-ua-001")
        config_change = engine.analyze_configuration_change(topology, "VOBJ-sip-ua-001")

        assert failure.severity == removal.severity == config_change.severity
        assert failure.impacted_objects == removal.impacted_objects == config_change.impacted_objects
        assert "Failure of" in failure.summary
        assert "Removal of" in removal.summary
        assert "Configuration change to" in config_change.summary
