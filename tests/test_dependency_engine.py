"""Tests for directed dependency traversal over voice topology graphs."""

from __future__ import annotations

import pytest

from model import DialPeer, Interface, Provider, SipUA, VoiceRelationship, VoiceService, VoiceTopology
from topology.dependency_engine import DependencyEngine
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


def _cyclic_topology() -> VoiceTopology:
    obj_a = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-a")
    obj_b = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        object_id="VOBJ-b",
    )
    obj_c = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        object_id="VOBJ-c",
    )
    relationships = (
        VoiceRelationship.create(RelationshipType.USES.value, obj_a.id, obj_b.id),
        VoiceRelationship.create(RelationshipType.USES.value, obj_b.id, obj_c.id),
        VoiceRelationship.create(RelationshipType.USES.value, obj_c.id, obj_a.id),
    )
    return VoiceTopology(
        sip_uas=(obj_a,),
        voice_services=(obj_b,),
        dial_peers=(obj_c,),
        relationships=relationships,
    )


class TestDependencyEngine:
    def test_direct_dependencies(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        assert engine.get_direct_dependencies(topology, "VOBJ-dial-peer-001") == (
            "VOBJ-provider-001",
            "VOBJ-voice-service-001",
        )
        assert engine.get_direct_dependencies(topology, "VOBJ-voice-service-001") == (
            "VOBJ-sip-ua-001",
        )
        assert engine.get_direct_dependencies(topology, "VOBJ-sip-ua-001") == (
            "VOBJ-interface-001",
        )

    def test_direct_dependents(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        assert engine.get_direct_dependents(topology, "VOBJ-voice-service-001") == (
            "VOBJ-dial-peer-001",
        )
        assert engine.get_direct_dependents(topology, "VOBJ-sip-ua-001") == (
            "VOBJ-voice-service-001",
        )
        assert engine.get_direct_dependents(topology, "VOBJ-interface-001") == (
            "VOBJ-sip-ua-001",
        )

    def test_transitive_dependencies(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        dependencies = engine.get_transitive_dependencies(topology, "VOBJ-dial-peer-001")

        assert dependencies == (
            "VOBJ-interface-001",
            "VOBJ-provider-001",
            "VOBJ-sip-ua-001",
            "VOBJ-voice-service-001",
        )

    def test_transitive_dependents(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        dependents = engine.get_transitive_dependents(topology, "VOBJ-sip-ua-001")

        assert dependents == (
            "VOBJ-dial-peer-001",
            "VOBJ-voice-service-001",
        )

    def test_explain_dependency_path(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        path = engine.explain_dependency_path(
            topology,
            "VOBJ-dial-peer-001",
            "VOBJ-sip-ua-001",
        )

        assert len(path) == 2
        assert path[0].source_object_id == "VOBJ-dial-peer-001"
        assert path[0].target_object_id == "VOBJ-voice-service-001"
        assert path[0].relationship_type == RelationshipType.USES.value
        assert path[1].source_object_id == "VOBJ-voice-service-001"
        assert path[1].target_object_id == "VOBJ-sip-ua-001"

    def test_explain_dependency_path_returns_empty_when_unreachable(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        path = engine.explain_dependency_path(
            topology,
            "VOBJ-interface-001",
            "VOBJ-dial-peer-001",
        )

        assert path == ()

    def test_missing_object_raises_typed_error(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        with pytest.raises(TopologyObjectNotFoundError) as exc_info:
            engine.get_direct_dependencies(topology, "VOBJ-missing")

        assert exc_info.value.object_id == "VOBJ-missing"

    def test_cycle_prevention_during_transitive_traversal(self) -> None:
        topology = _cyclic_topology()
        engine = DependencyEngine()

        dependencies = engine.get_transitive_dependencies(topology, "VOBJ-a")
        dependents = engine.get_transitive_dependents(topology, "VOBJ-a")

        assert dependencies == ("VOBJ-b", "VOBJ-c")
        assert dependents == ("VOBJ-b", "VOBJ-c")

    def test_transitive_traversal_respects_max_depth(self) -> None:
        topology = _full_chain_topology()
        engine = DependencyEngine()

        dependencies = engine.get_transitive_dependencies(
            topology,
            "VOBJ-dial-peer-001",
            max_depth=1,
        )

        assert dependencies == ("VOBJ-provider-001", "VOBJ-voice-service-001")
