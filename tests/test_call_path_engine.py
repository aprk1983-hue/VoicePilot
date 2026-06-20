"""Tests for deterministic call path modeling over voice topology graphs."""

from __future__ import annotations

from model import DialPeer, Interface, Provider, SipUA, VoiceService
from topology.call_path_engine import CallPathEngine
from topology.call_path_models import CallPathDirection
from topology.relationship_types import RelationshipType
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


def _full_chain_topology(*, sip_ua_enabled: bool | None = False):
    sip_ua = SipUA.create(
        **_provenance(),
        enabled=sip_ua_enabled,
        object_id="VOBJ-sip-ua-001",
    )
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        object_id="VOBJ-voice-service-001",
    )
    dial_peer_a = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        session_target="ipv4:192.0.2.10",
        object_id="VOBJ-dial-peer-a",
    )
    dial_peer_b = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=2,
        session_target="ipv4:198.51.100.20",
        object_id="VOBJ-dial-peer-b",
    )
    interface = Interface.create(
        **_provenance(
            source_parser="cisco_show_version",
            source_command="show version",
        ),
        name="GigabitEthernet0/0",
        object_id="VOBJ-interface-001",
    )
    provider_a = Provider.create(
        **_provenance(),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-a",
    )
    provider_b = Provider.create(
        **_provenance(),
        name="ITSP-Secondary",
        addresses=("ipv4:198.51.100.20",),
        object_id="VOBJ-provider-b",
    )
    topology = TopologyBuilder().build(
        [dial_peer_b, dial_peer_a, voice_service, sip_ua, interface, provider_a, provider_b]
    )
    return topology, dial_peer_a, dial_peer_b, provider_a, provider_b, sip_ua


class TestCallPathEngine:
    def test_path_from_dial_peer_to_provider(self) -> None:
        topology, dial_peer_a, _, provider_a, _, _ = _full_chain_topology()
        engine = CallPathEngine()

        call_path = engine.build_path(
            topology,
            dial_peer_a.id,
            provider_a.id,
            direction=CallPathDirection.OUTBOUND,
        )

        assert call_path.direction == CallPathDirection.OUTBOUND
        assert call_path.source_object_id == dial_peer_a.id
        assert call_path.destination_object_id == provider_a.id
        assert len(call_path.hops) == 2
        assert call_path.hops[0].object_id == dial_peer_a.id
        assert call_path.hops[0].relationship_to_next == RelationshipType.ROUTES_TO.value
        assert call_path.hops[1].object_id == provider_a.id
        assert call_path.hops[1].relationship_to_next is None
        assert call_path.warnings == ()
        assert "Call path from dial-peer 1 to ITSP-Primary" in call_path.summary

    def test_outbound_paths_from_all_dial_peers_routing_to_providers(self) -> None:
        topology, dial_peer_a, dial_peer_b, provider_a, provider_b, _ = _full_chain_topology()
        engine = CallPathEngine()

        outbound_paths = engine.build_outbound_paths(topology)

        assert len(outbound_paths) == 2
        assert outbound_paths[0].source_object_id == dial_peer_a.id
        assert outbound_paths[0].destination_object_id == provider_a.id
        assert outbound_paths[1].source_object_id == dial_peer_b.id
        assert outbound_paths[1].destination_object_id == provider_b.id
        assert all(path.direction == CallPathDirection.OUTBOUND for path in outbound_paths)

    def test_no_path_returns_warning_without_crashing(self) -> None:
        topology, dial_peer_a, _, provider_a, _, _ = _full_chain_topology()
        engine = CallPathEngine()

        call_path = engine.build_path(topology, provider_a.id, dial_peer_a.id)

        assert call_path.hops == ()
        assert call_path.warnings
        assert "No dependency path found" in call_path.warnings[0]
        assert "No call path from ITSP-Primary to dial-peer 1" in call_path.summary

    def test_hop_construction_for_multi_hop_dependency_path(self) -> None:
        topology, dial_peer_a, _, _, _, sip_ua = _full_chain_topology()
        engine = CallPathEngine()

        call_path = engine.build_path(topology, dial_peer_a.id, sip_ua.id)

        assert len(call_path.hops) == 3
        assert [hop.object_id for hop in call_path.hops] == [
            dial_peer_a.id,
            "VOBJ-voice-service-001",
            sip_ua.id,
        ]
        assert call_path.hops[0].relationship_to_next == RelationshipType.USES.value
        assert call_path.hops[1].relationship_to_next == RelationshipType.USES.value
        assert call_path.hops[2].relationship_to_next is None
        assert call_path.hops[0].label == "dial-peer 1"
        assert call_path.hops[2].object_type == "sip_ua"

    def test_breakpoint_detection_for_disabled_sip_ua(self) -> None:
        topology, dial_peer_a, _, provider_a, _, sip_ua = _full_chain_topology(sip_ua_enabled=False)
        engine = CallPathEngine()

        call_path = engine.build_path(topology, dial_peer_a.id, sip_ua.id)
        breakpoints = engine.find_breakpoints(call_path)

        assert len(breakpoints) == 1
        assert breakpoints[0].object_id == sip_ua.id
        assert breakpoints[0].health_status == "disabled"
        assert "disabled" in breakpoints[0].findings

    def test_breakpoints_empty_when_no_health_metadata(self) -> None:
        topology, dial_peer_a, _, provider_a, _, _ = _full_chain_topology(sip_ua_enabled=None)
        engine = CallPathEngine()

        call_path = engine.build_path(topology, dial_peer_a.id, provider_a.id)
        for hop in call_path.hops:
            assert hop.health_status == "unknown"
            assert hop.findings == ()
            assert hop.metadata == {}

        assert engine.find_breakpoints(call_path) == ()

    def test_deterministic_ordering_for_outbound_paths(self) -> None:
        topology, dial_peer_a, dial_peer_b, provider_a, provider_b, _ = _full_chain_topology()
        engine = CallPathEngine()

        first = engine.build_outbound_paths(topology)
        second = engine.build_outbound_paths(topology)

        assert first == second
        assert [path.id for path in first] == [
            f"CPATH-{dial_peer_a.id}-{provider_a.id}",
            f"CPATH-{dial_peer_b.id}-{provider_b.id}",
        ]

    def test_missing_source_returns_warning_without_crashing(self) -> None:
        topology, _, _, provider_a, _, _ = _full_chain_topology()
        engine = CallPathEngine()

        call_path = engine.build_path(topology, "VOBJ-missing", provider_a.id)

        assert call_path.hops == ()
        assert "Source object not found" in call_path.warnings[0]
