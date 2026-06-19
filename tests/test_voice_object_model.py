"""Tests for Canonical Voice Object Model (CVOM) v1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from model import (
    Device,
    DialPeer,
    Interface,
    ObjectRegistry,
    Provider,
    SipUA,
    VoiceRelationship,
    VoiceService,
    VoiceTopology,
)
from model.object_registry import ObjectRegistryError
from model.voice_graph import OBJECT_TYPE_DIAL_PEER, OBJECT_TYPE_SIP_UA, VoiceObject


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


class TestDevice:
    def test_device_with_interfaces(self) -> None:
        iface = Interface.create(
            **_provenance(
                source_parser="cisco_show_version",
                source_command="show version",
            ),
            name="GigabitEthernet0/0",
            ip="10.1.1.10",
            mask="255.255.255.0",
            status="up",
        )
        device = Device.create(
            **_provenance(),
            ios_version="17.9.1",
            model="ISR4451",
            management_ip="10.1.1.10",
            interfaces=(iface,),
        )

        assert device.object_type == "device"
        assert device.hostname == "cube-edge-01"
        assert device.ios_version == "17.9.1"
        assert len(device.interfaces) == 1
        assert device.interfaces[0].name == "GigabitEthernet0/0"


class TestDialPeer:
    def test_dial_peer_fields(self) -> None:
        peer = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=1001,
            peer_type="voip",
            destination_pattern="9T",
            session_target="sip:provider.example.com",
            status="up",
        )

        assert peer.object_type == OBJECT_TYPE_DIAL_PEER
        assert peer.tag == 1001
        assert peer.destination_pattern == "9T"
        assert peer.id.startswith("VOBJ-")


class TestSipUA:
    def test_sip_ua_disabled(self) -> None:
        sip_ua = SipUA.create(
            **_provenance(),
            enabled=False,
            registered=False,
            registrar="sip:provider.example.com",
            transport="udp",
        )

        assert sip_ua.object_type == OBJECT_TYPE_SIP_UA
        assert sip_ua.enabled is False
        assert sip_ua.registered is False
        assert sip_ua.source_parser == "cisco_show_sip_ua_status"


class TestVoiceService:
    def test_voice_service_config(self) -> None:
        service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=True,
            bind_control="source-interface GigabitEthernet0/0",
            trusted_ips=("10.0.0.0/8",),
            supplementary_services=("t38",),
        )

        assert service.object_type == "voice_service"
        assert service.bind_control is not None
        assert "10.0.0.0/8" in service.trusted_ips


class TestObjectRegistry:
    def test_register_and_lookup_by_id_type_hostname_parser(self) -> None:
        registry = ObjectRegistry()
        sip_ua = SipUA.create(**_provenance(), enabled=False)
        dial_peer = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=1,
        )

        registry.register(sip_ua)
        registry.register(dial_peer)

        assert registry.get_by_id(sip_ua.id) is sip_ua
        assert len(registry.list_by_type(OBJECT_TYPE_SIP_UA)) == 1
        assert len(registry.list_by_hostname("cube-edge-01")) == 2
        assert len(registry.list_by_parser("cisco_show_sip_ua_status")) == 1
        assert len(registry) == 2

    def test_registry_rejects_duplicate_id(self) -> None:
        registry = ObjectRegistry()
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-fixed123456")
        registry.register(sip_ua)

        duplicate = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-fixed123456")
        with pytest.raises(ObjectRegistryError):
            registry.register(duplicate)


class TestRelationships:
    def test_voice_topology_with_relationships(self) -> None:
        device = Device.create(**_provenance())
        peer = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=2001,
        )
        provider = Provider.create(
            **_provenance(),
            name="ITSP-Primary",
            transport="tls",
            addresses=("sip:trunk.example.com",),
            status="up",
        )
        relationship = VoiceRelationship.create(
            "terminates_on",
            peer.id,
            provider.id,
            description="Dial-peer 2001 targets provider trunk",
        )

        topology = VoiceTopology(
            devices=(device,),
            providers=(provider,),
            dial_peers=(peer,),
            relationships=(relationship,),
        )

        assert topology.object_count == 3
        assert len(topology.relationships) == 1
        assert topology.relationships[0].relationship_type == "terminates_on"
        assert topology.relationships[0].source_object_id == peer.id


class TestImmutability:
    def test_voice_objects_are_frozen(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False)

        with pytest.raises(FrozenInstanceError):
            sip_ua.enabled = True  # type: ignore[misc]

    def test_replace_creates_new_instance(self) -> None:
        sip_ua = SipUA.create(**_provenance(), enabled=False)
        updated = replace(sip_ua, enabled=True)

        assert sip_ua.enabled is False
        assert updated.enabled is True
        assert updated.id == sip_ua.id

    def test_voice_object_confidence_bounds(self) -> None:
        with pytest.raises(ValueError):
            SipUA.create(**_provenance(), enabled=True, confidence=150.0)

    def test_base_voice_object_provenance(self) -> None:
        obj: VoiceObject = SipUA.create(**_provenance(), enabled=True, confidence=95.0)

        assert obj.vendor == "cisco"
        assert obj.platform == "CUBE"
        assert obj.source_evidence_id == "EVD-test-001"
        assert obj.confidence == 95.0
