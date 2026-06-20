"""Integration tests for bundled Cisco knowledge packs."""

from __future__ import annotations

from pathlib import Path

import pytest

from knowledge import KnowledgeEngine, KnowledgeLoader, KnowledgeRegistry
from model import DialPeer, SipUA, VoiceService
from runtime.knowledge_bootstrap import (
    PACKS_ROOT,
    load_default_knowledge_packs,
    reset_default_knowledge_engine,
)
from topology.topology_builder import TopologyBuilder

CISCO_PACKS_DIR = PACKS_ROOT / "cisco" / "best-practices"


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


@pytest.fixture(autouse=True)
def _reset_knowledge_cache() -> None:
    reset_default_knowledge_engine()
    yield
    reset_default_knowledge_engine()


class TestCiscoKnowledgePacks:
    def test_knowledge_packs_load_from_yaml(self) -> None:
        registry = load_default_knowledge_packs()

        assert registry.get("CISCO-BP-SIP-UA-ENABLED") is not None
        assert registry.get("CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS") is not None
        assert registry.get("CISCO-BP-DIAL-PEER-DESTINATION-PATTERN") is not None

    def test_loader_reads_cisco_best_practices_directory(self) -> None:
        loader = KnowledgeLoader()
        packs = loader.load_directory(CISCO_PACKS_DIR)

        assert len(packs) == 3
        assert {pack.id for pack in packs} == {
            "CISCO-BP-SIP-UA-ENABLED",
            "CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS",
            "CISCO-BP-DIAL-PEER-DESTINATION-PATTERN",
        }

    def test_disabled_sip_ua_matches_cisco_bp_sip_ua_enabled(self) -> None:
        registry = load_default_knowledge_packs()
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        engine = KnowledgeEngine(registry)

        matches = engine.evaluate_object(sip_ua)

        assert len(matches) == 1
        assert matches[0].pack_id == "CISCO-BP-SIP-UA-ENABLED"
        assert "Enable SIP-UA and verify SIP registration" in matches[0].recommendations[0]

    def test_voice_service_missing_allow_connections_matches_pack(self) -> None:
        registry = load_default_knowledge_packs()
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=None,
            object_id="VOBJ-voice-service-001",
        )
        engine = KnowledgeEngine(registry)

        matches = engine.evaluate_object(voice_service)

        assert len(matches) == 1
        assert matches[0].pack_id == "CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS"

    def test_voice_service_allow_connections_false_matches_pack(self) -> None:
        registry = load_default_knowledge_packs()
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=False,
            object_id="VOBJ-voice-service-001",
        )
        engine = KnowledgeEngine(registry)

        matches = engine.evaluate_object(voice_service)

        assert len(matches) == 1
        assert matches[0].pack_id == "CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS"

    def test_dial_peer_missing_destination_pattern_matches_pack(self) -> None:
        registry = load_default_knowledge_packs()
        dial_peer = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=1,
            destination_pattern="",
            object_id="VOBJ-dial-peer-001",
        )
        engine = KnowledgeEngine(registry)

        matches = engine.evaluate_object(dial_peer)

        assert len(matches) == 1
        assert matches[0].pack_id == "CISCO-BP-DIAL-PEER-DESTINATION-PATTERN"

    def test_dial_peer_with_destination_pattern_does_not_match(self) -> None:
        registry = load_default_knowledge_packs()
        dial_peer = DialPeer.create(
            **_provenance(
                source_parser="cisco_show_dial_peer_voice_summary",
                source_command="show dial-peer voice summary",
            ),
            tag=1,
            destination_pattern="9T",
            object_id="VOBJ-dial-peer-001",
        )
        engine = KnowledgeEngine(registry)

        matches = engine.evaluate_object(dial_peer)

        assert matches == ()

    def test_topology_evaluation_is_deterministic(self) -> None:
        registry = load_default_knowledge_packs()
        sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
        voice_service = VoiceService.create(
            **_provenance(
                source_parser="cisco_show_run_voice_service_voip",
                source_command="show run | sec voice service voip",
            ),
            allow_connections=None,
            object_id="VOBJ-voice-service-001",
        )
        topology = TopologyBuilder().build([voice_service, sip_ua])
        engine = KnowledgeEngine(registry)

        first = engine.evaluate_topology(topology)
        second = engine.evaluate_topology(topology)

        assert first.matched_packs == second.matched_packs
        assert [match.pack_id for match in first.matched_packs] == [
            "CISCO-BP-SIP-UA-ENABLED",
            "CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS",
        ]
