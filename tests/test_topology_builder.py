"""Tests for assembling immutable voice topology graphs."""

from __future__ import annotations

from model import DialPeer, Interface, Provider, SipUA, VoiceService, VoiceTopology
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


class TestTopologyBuilder:
    def test_empty_topology(self) -> None:
        topology = TopologyBuilder().build([])

        assert isinstance(topology, VoiceTopology)
        assert topology.object_count == 0
        assert topology.relationships == ()
        assert topology.all_objects() == ()

    def test_single_sip_ua_topology(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")

        topology = TopologyBuilder().build([sip_ua])

        assert topology.object_count == 1
        assert topology.sip_uas == (sip_ua,)
        assert topology.relationships == ()

    def test_sip_ua_and_voice_service_topology(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            object_id="VOBJ-voice-service-001",
        )

        topology = TopologyBuilder().build([voice_service, sip_ua])

        assert topology.object_count == 2
        assert topology.voice_services == (voice_service,)
        assert topology.sip_uas == (sip_ua,)
        assert len(topology.relationships) == 1

    def test_dial_peer_voice_service_sip_ua_topology(self) -> None:
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
            object_id="VOBJ-dial-peer-001",
        )

        topology = TopologyBuilder().build([dial_peer, voice_service, sip_ua])

        assert topology.object_count == 3
        assert topology.dial_peers == (dial_peer,)
        assert len(topology.relationships) == 2

    def test_topology_includes_interface_and_provider_objects(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
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
            object_id="VOBJ-provider-001",
        )

        topology = TopologyBuilder().build([sip_ua, interface, provider])

        assert topology.object_count == 3
        assert topology.interfaces == (interface,)
        assert topology.providers == (provider,)
        assert len(topology.relationships) == 1
        assert topology.relationships[0].relationship_type == "binds_to"

    def test_duplicate_build_is_idempotent(self) -> None:
        builder = TopologyBuilder()
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            object_id="VOBJ-voice-service-001",
        )
        objects = [voice_service, sip_ua]

        first = builder.build(objects)
        second = builder.build(objects)

        assert first.object_count == second.object_count == 2
        assert len(first.relationships) == len(second.relationships) == 1
        assert {
            (rel.source_object_id, rel.target_object_id, rel.relationship_type)
            for rel in first.relationships
        } == {
            (rel.source_object_id, rel.target_object_id, rel.relationship_type)
            for rel in second.relationships
        }

    def test_objects_are_sorted_deterministically_by_id(self) -> None:
        dial_peer_b = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=2,
            object_id="VOBJ-dial-peer-b",
        )
        dial_peer_a = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=1,
            object_id="VOBJ-dial-peer-a",
        )

        topology = TopologyBuilder().build([dial_peer_b, dial_peer_a])

        assert [peer.id for peer in topology.dial_peers] == ["VOBJ-dial-peer-a", "VOBJ-dial-peer-b"]
