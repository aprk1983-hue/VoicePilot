"""Tests for high-level voice topology query helpers."""

from __future__ import annotations

import pytest

from model import DialPeer, Provider, SipUA, VoiceService
from topology.topology_builder import TopologyBuilder
from topology.topology_exceptions import TopologyObjectNotFoundError
from topology.topology_queries import TopologyQueries


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
        [dial_peer_b, dial_peer_a, voice_service, sip_ua, provider_a, provider_b]
    )
    return topology, dial_peer_a, dial_peer_b, voice_service, sip_ua, provider_a


class TestTopologyQueries:
    def test_find_dial_peers_using_voice_service(self) -> None:
        topology, dial_peer_a, dial_peer_b, *_ = _sample_topology()
        queries = TopologyQueries()

        dial_peers = queries.find_dial_peers_using_voice_service(topology)

        assert dial_peers == (dial_peer_a, dial_peer_b)

    def test_find_dial_peers_routing_to_provider(self) -> None:
        topology, dial_peer_a, dial_peer_b, _, _, provider = _sample_topology()
        queries = TopologyQueries()

        dial_peers = queries.find_dial_peers_routing_to_provider(topology, provider.id)

        assert dial_peers == (dial_peer_a,)

    def test_find_dial_peers_routing_to_missing_provider_raises(self) -> None:
        topology, *_ = _sample_topology()
        queries = TopologyQueries()

        with pytest.raises(TopologyObjectNotFoundError):
            queries.find_dial_peers_routing_to_provider(topology, "VOBJ-missing")

    def test_find_objects_depending_on_sipua(self) -> None:
        topology, dial_peer_a, dial_peer_b, voice_service, sip_ua, _ = _sample_topology()
        queries = TopologyQueries()

        dependents = queries.find_objects_depending_on_sipua(topology)

        assert [obj.id for obj in dependents] == [
            dial_peer_a.id,
            dial_peer_b.id,
            voice_service.id,
        ]
        assert sip_ua.id not in {obj.id for obj in dependents}

    def test_find_dial_peers_using_voice_service_empty_without_voice_service(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        topology = TopologyBuilder().build([sip_ua])
        queries = TopologyQueries()

        assert queries.find_dial_peers_using_voice_service(topology) == ()

    def test_find_objects_depending_on_sipua_empty_without_sip_ua(self) -> None:
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            object_id="VOBJ-voice-service-001",
        )
        topology = TopologyBuilder().build([voice_service])
        queries = TopologyQueries()

        assert queries.find_objects_depending_on_sipua(topology) == ()
