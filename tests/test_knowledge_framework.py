"""Tests for the Voice Knowledge Framework core."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from knowledge import (
    DuplicateKnowledgePackError,
    KnowledgeCategory,
    KnowledgeEngine,
    KnowledgeLoader,
    KnowledgeRegistry,
    KnowledgeSchemaError,
    KnowledgeSeverity,
)
from knowledge.knowledge_pack import build_knowledge_pack
from knowledge.knowledge_matcher import KnowledgeMatcher
from model import DialPeer, Provider, SipUA, VoiceService
from topology.topology_builder import TopologyBuilder


SAMPLE_PACK = {
    "id": "cisco-sip-ua-disabled",
    "title": "SIP-UA disabled operational guidance",
    "description": "Guidance when SIP-UA is administratively disabled.",
    "vendor": "cisco",
    "platform": "CUBE",
    "category": "operations",
    "severity": "critical",
    "supported_object_types": ["sip_ua"],
    "conditions": {"enabled": False},
    "recommendations": [
        "Enable SIP-UA and verify SIP registration.",
        "Review voice service voip configuration.",
    ],
    "references": ["https://example.com/cube/sip-ua"],
    "metadata": {"source": "vkf-test"},
    "version": "1.0",
}

DIAL_PEER_PACK = {
    "id": "cisco-dial-peer-no-destination",
    "title": "Dial peer missing destination pattern",
    "description": "Dial peers require destination patterns.",
    "vendor": "cisco",
    "platform": "CUBE",
    "category": "configuration",
    "severity": "high",
    "supported_object_types": ["dial_peer"],
    "conditions": {"destination_pattern": ""},
    "recommendations": ["Configure destination-pattern on the dial peer."],
    "references": [],
    "version": "1.0",
}


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
    dial_peer = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        destination_pattern="",
        object_id="VOBJ-dial-peer-001",
    )
    provider = Provider.create(
        **_provenance(),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-001",
    )
    return TopologyBuilder().build([dial_peer, voice_service, sip_ua, provider])


def _registry_with_sample_packs() -> KnowledgeRegistry:
    registry = KnowledgeRegistry()
    registry.register(build_knowledge_pack(SAMPLE_PACK))
    registry.register(build_knowledge_pack(DIAL_PEER_PACK))
    return registry


class TestKnowledgeRegistry:
    def test_register_and_lookup(self) -> None:
        registry = KnowledgeRegistry()
        pack = build_knowledge_pack(SAMPLE_PACK)

        registry.register(pack)

        assert registry.get("cisco-sip-ua-disabled") == pack

    def test_search_by_object_type(self) -> None:
        registry = _registry_with_sample_packs()

        sip_packs = registry.search_by_object_type("sip_ua")
        dial_peer_packs = registry.search_by_object_type("dial_peer")

        assert [pack.id for pack in sip_packs] == ["cisco-sip-ua-disabled"]
        assert [pack.id for pack in dial_peer_packs] == ["cisco-dial-peer-no-destination"]

    def test_prevent_duplicate_ids(self) -> None:
        registry = KnowledgeRegistry()
        registry.register(build_knowledge_pack(SAMPLE_PACK))

        with pytest.raises(DuplicateKnowledgePackError):
            registry.register(build_knowledge_pack(SAMPLE_PACK))


class TestKnowledgeSchema:
    def test_validation_rejects_missing_fields(self) -> None:
        with pytest.raises(KnowledgeSchemaError):
            build_knowledge_pack({"id": "incomplete"})

    def test_validation_rejects_invalid_category(self) -> None:
        invalid = dict(SAMPLE_PACK)
        invalid["category"] = "not-a-category"

        with pytest.raises(KnowledgeSchemaError):
            build_knowledge_pack(invalid)


class TestKnowledgeLoader:
    def test_load_yaml_pack(self, tmp_path: Path) -> None:
        pack_path = tmp_path / "cisco-sip-ua-disabled.yaml"
        pack_path.write_text(
            "\n".join(
                [
                    "id: cisco-sip-ua-disabled",
                    "title: SIP-UA disabled operational guidance",
                    "description: Guidance when SIP-UA is administratively disabled.",
                    "vendor: cisco",
                    "platform: CUBE",
                    "category: operations",
                    "severity: critical",
                    "supported_object_types:",
                    "  - sip_ua",
                    "conditions:",
                    "  enabled: false",
                    "recommendations:",
                    "  - Enable SIP-UA and verify SIP registration.",
                    "references:",
                    "  - https://example.com/cube/sip-ua",
                    "version: '1.0'",
                ]
            ),
            encoding="utf-8",
        )

        loader = KnowledgeLoader()
        pack = loader.load_file(pack_path)

        assert pack.id == "cisco-sip-ua-disabled"
        assert loader.registry.get(pack.id) is pack


class TestKnowledgeMatcher:
    def test_match_disabled_sip_ua(self) -> None:
        topology = _sample_topology()
        matcher = KnowledgeMatcher(_registry_with_sample_packs())

        matches = matcher.match_topology(topology)

        assert any(match.pack_id == "cisco-sip-ua-disabled" for match in matches)
        assert any(match.pack_id == "cisco-dial-peer-no-destination" for match in matches)

    def test_deterministic_ordering(self) -> None:
        topology = _sample_topology()
        matcher = KnowledgeMatcher(_registry_with_sample_packs())

        first = matcher.match_topology(topology)
        second = matcher.match_topology(topology)

        assert first == second
        assert [match.pack_id for match in first] == sorted(match.pack_id for match in first)


class TestKnowledgeEngine:
    def test_evaluate_object(self) -> None:
        topology = _sample_topology()
        sip_ua = topology.sip_uas[0]
        engine = KnowledgeEngine(_registry_with_sample_packs())

        matches = engine.evaluate_object(sip_ua)

        assert len(matches) == 1
        assert matches[0].pack_id == "cisco-sip-ua-disabled"

    def test_evaluate_topology(self) -> None:
        engine = KnowledgeEngine(_registry_with_sample_packs())
        report = engine.evaluate_topology(_sample_topology())

        assert len(report.matched_packs) == 2
        assert "Enable SIP-UA and verify SIP registration." in report.recommendations
        assert "https://example.com/cube/sip-ua" in report.references
        assert report.summary == "Matched 2 knowledge packs."

    def test_evaluate_case(self) -> None:
        topology = _sample_topology()
        case = Case(
            case_id="CASE-VKF-001",
            title="knowledge test",
            status=InvestigationState.ANALYSIS,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="outbound calls fail"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
            voice_objects=list(topology.all_objects()),
        )
        engine = KnowledgeEngine(_registry_with_sample_packs())

        report = engine.evaluate_case(case)

        assert len(report.matched_packs) == 2
        by_id = {match.pack_id: match for match in report.matched_packs}
        assert by_id["cisco-sip-ua-disabled"].severity == KnowledgeSeverity.CRITICAL
        assert by_id["cisco-sip-ua-disabled"].category == KnowledgeCategory.OPERATIONS
        assert by_id["cisco-dial-peer-no-destination"].severity == KnowledgeSeverity.HIGH
