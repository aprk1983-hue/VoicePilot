"""Tests for deterministic relationship inference over CVOM objects."""

from __future__ import annotations

from model import DialPeer, Interface, Provider, SipUA, VoiceService
from topology.relationship_builder import RelationshipBuilder
from topology.relationship_types import RelationshipType


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


def _sip_ua(**overrides: str) -> SipUA:
    return SipUA.create(**_provenance(**overrides), enabled=False, object_id="VOBJ-sip-ua-001")


def _voice_service(**overrides: str) -> VoiceService:
    object_id = overrides.pop("object_id", "VOBJ-voice-service-001")
    return VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
            **overrides,
        ),
        object_id=object_id,
    )


def _dial_peer(**overrides: str) -> DialPeer:
    object_id = overrides.pop("object_id", "VOBJ-dial-peer-001")
    session_target = overrides.pop("session_target", None)
    return DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
            **overrides,
        ),
        tag=1,
        destination_pattern="9T",
        session_target=session_target,
        object_id=object_id,
    )


def _interface(**overrides: str) -> Interface:
    return Interface.create(
        **_provenance(
            source_parser="cisco_show_version",
            source_command="show version",
            **overrides,
        ),
        name="GigabitEthernet0/0",
        ip="10.1.1.10",
        object_id="VOBJ-interface-001",
    )


def _provider(**overrides: str) -> Provider:
    return Provider.create(
        **_provenance(
            source_parser="cisco_show_sip_ua_status",
            source_command="show sip-ua status",
            **overrides,
        ),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-001",
    )


class TestRelationshipBuilder:
    def test_empty_input_returns_no_relationships(self) -> None:
        relationships = RelationshipBuilder().build([])

        assert relationships == ()

    def test_single_sip_ua_has_no_relationships(self) -> None:
        relationships = RelationshipBuilder().build([_sip_ua()])

        assert relationships == ()

    def test_voice_service_uses_sip_ua_when_both_present(self) -> None:
        sip_ua = _sip_ua()
        voice_service = _voice_service()

        relationships = RelationshipBuilder().build([sip_ua, voice_service])

        assert len(relationships) == 1
        assert relationships[0].relationship_type == RelationshipType.USES.value
        assert relationships[0].source_object_id == voice_service.id
        assert relationships[0].target_object_id == sip_ua.id

    def test_dial_peer_voice_service_and_sip_ua_chain(self) -> None:
        sip_ua = _sip_ua()
        voice_service = _voice_service()
        dial_peer = _dial_peer()

        relationships = RelationshipBuilder().build([dial_peer, voice_service, sip_ua])

        assert len(relationships) == 2
        uses_relationships = [
            rel for rel in relationships if rel.relationship_type == RelationshipType.USES.value
        ]
        assert len(uses_relationships) == 2
        assert any(
            rel.source_object_id == dial_peer.id and rel.target_object_id == voice_service.id
            for rel in uses_relationships
        )
        assert any(
            rel.source_object_id == voice_service.id and rel.target_object_id == sip_ua.id
            for rel in uses_relationships
        )

    def test_sip_ua_binds_to_interface_on_same_hostname(self) -> None:
        sip_ua = _sip_ua()
        interface = _interface()

        relationships = RelationshipBuilder().build([sip_ua, interface])

        assert len(relationships) == 1
        assert relationships[0].relationship_type == RelationshipType.BINDS_TO.value
        assert relationships[0].source_object_id == sip_ua.id
        assert relationships[0].target_object_id == interface.id

    def test_sip_ua_does_not_bind_to_interface_on_different_hostname(self) -> None:
        sip_ua = _sip_ua()
        interface = _interface(hostname="cube-edge-02")

        relationships = RelationshipBuilder().build([sip_ua, interface])

        assert relationships == ()

    def test_dial_peer_routes_to_single_provider(self) -> None:
        dial_peer = _dial_peer(session_target="ipv4:198.51.100.20")
        provider = _provider()

        relationships = RelationshipBuilder().build([dial_peer, provider])

        assert len(relationships) == 1
        assert relationships[0].relationship_type == RelationshipType.ROUTES_TO.value
        assert relationships[0].source_object_id == dial_peer.id
        assert relationships[0].target_object_id == provider.id

    def test_multiple_voice_services_omits_dial_peer_uses_rule(self) -> None:
        dial_peer = _dial_peer()
        voice_service_a = _voice_service(object_id="VOBJ-voice-service-a")
        voice_service_b = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            object_id="VOBJ-voice-service-b",
        )

        relationships = RelationshipBuilder().build(
            [dial_peer, voice_service_a, voice_service_b]
        )

        assert relationships == ()

    def test_duplicate_prevention_on_repeated_build(self) -> None:
        builder = RelationshipBuilder()
        objects = [_dial_peer(), _voice_service(), _sip_ua()]

        first = builder.build(objects)
        second = builder.build(objects)

        assert len(first) == 2
        assert len(second) == 2
        assert {(rel.source_object_id, rel.target_object_id, rel.relationship_type) for rel in first} == {
            (rel.source_object_id, rel.target_object_id, rel.relationship_type) for rel in second
        }

    def test_full_topology_relationship_counts(self) -> None:
        objects = [
            _dial_peer(session_target="ipv4:192.0.2.10"),
            _voice_service(),
            _sip_ua(),
            _interface(),
            _provider(),
        ]

        relationships = RelationshipBuilder().build(objects)

        assert len(relationships) == 4
        relationship_types = {rel.relationship_type for rel in relationships}
        assert relationship_types == {
            RelationshipType.USES.value,
            RelationshipType.BINDS_TO.value,
            RelationshipType.ROUTES_TO.value,
        }
