"""Tests for Cisco show run voice service voip parser."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "parser"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core"))

from domain.enums import InvestigationState, Severity
from domain.models import Case, Evidence
from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary
from model.voice_service import VoiceService
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers
from plugins.cisco.parser.show_run_voice_service_voip import CiscoShowRunVoiceServiceVoipParser
from runtime.analysis_engine import AnalysisEngine, FINDING_SOURCE_PARSER


@pytest.fixture
def parser() -> CiscoShowRunVoiceServiceVoipParser:
    return CiscoShowRunVoiceServiceVoipParser()


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-cisco-voice-svc",
        evidence_id="EVD-voice-svc-parser",
        device_id="DEV-cube-01",
        platform="CUBE",
        ios_version="17.9.1",
        hostname="cube-edge-01",
    )


@pytest.fixture
def cisco_registry() -> ParserRegistry:
    registry = ParserRegistry()
    register_cisco_parsers(registry)
    yield registry
    registry.clear()


def _signals(result) -> set[str]:
    return {finding.signal for finding in result.findings}


class TestCiscoShowRunVoiceServiceVoipParser:
    def test_detects_voice_service_voip_config(self, parser: CiscoShowRunVoiceServiceVoipParser) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        assert parser.detect(raw)

    def test_detects_voice_service_and_sip_section(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["voice_service_voip_present"] is True
        assert result.structured_data["sip_section_present"] is True
        assert "voice_service_voip_present" in _signals(result)
        assert "sip_section_present" in _signals(result)

    def test_detects_sip_disabled_by_config(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_disabled.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["sip_ua_disabled_by_config"] is True
        assert result.structured_data["sip_section_present"] is False
        assert "sip_ua_disabled_by_config" in _signals(result)

    def test_extracts_bind_control_interface(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["bind_control_interface"] == "Loopback0"
        assert "sip_bind_control_present" in _signals(result)

    def test_extracts_bind_media_interface(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["bind_media_interface"] == "GigabitEthernet0/0/1"
        assert "sip_bind_media_present" in _signals(result)

    def test_detects_trusted_ip_list(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["trusted_ip_list_present"] is True
        assert result.structured_data["trusted_ips"] == ["192.0.2.0 255.255.255.0"]
        assert "trusted_ip_list_present" in _signals(result)

    def test_detects_allow_connections_sip_to_sip(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["allow_connections_sip_to_sip"] is True
        assert "allow_connections_sip_to_sip_present" in _signals(result)

    def test_detects_early_offer_and_options_ping(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["early_offer_forced"] is True
        assert result.structured_data["options_ping_present"] is True
        assert "early_offer_forced" in _signals(result)
        assert "options_ping_present" in _signals(result)

    def test_parser_engine_runs_when_registered(
        self,
        cisco_registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_disabled.txt").read_text(encoding="utf-8")
        engine = ParserEngine(registry=cisco_registry)
        result = engine.parse(raw, parser_context, command="show run | sec voice service voip")

        assert result.command == "show run | sec voice service voip"
        assert result.structured_data["sip_ua_disabled_by_config"] is True

    def test_analysis_engine_uses_parser_for_voice_service_voip(
        self,
        cisco_registry: ParserRegistry,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_disabled.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Voice service parser integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        case.status = InvestigationState.ANALYSIS
        case.evidence.append(
            Evidence(
                evidence_id="EVD-voice-svc",
                case_id=case.case_id,
                type="cli_output",
                title="CLI paste",
                source=EvidenceSource(
                    origin="cli_paste",
                    collector="engineer",
                    command="show run | sec voice service voip",
                ),
                collected_at=case.opened_at,
                quality=EvidenceQuality(
                    completeness=1.0,
                    freshness=1.0,
                    reliability=1.0,
                    parseability=1.0,
                    overall=1.0,
                ),
                raw_text=raw,
            )
        )

        findings = AnalysisEngine(parser_engine=ParserEngine(registry=cisco_registry)).analyze(case)
        disabled_finding = next(f for f in findings if f.signal == "sip_ua_disabled_by_config")

        assert disabled_finding.metadata is not None
        assert disabled_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert (
            disabled_finding.metadata["parser_id"] == "cisco_show_run_voice_service_voip"
        )
        assert "related_voice_object_ids" in disabled_finding.metadata
        assert len(disabled_finding.metadata["related_voice_object_ids"]) == 1
        assert disabled_finding.metadata["related_voice_object_ids"][0].startswith("VOBJ-")

    def test_does_not_detect_sip_ua_status_output(self, parser: CiscoShowRunVoiceServiceVoipParser) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        assert not parser.detect(raw)


class TestCiscoShowRunVoiceServiceVoipParserCvom:
    def _voice_service(self, result) -> VoiceService:
        assert len(result.voice_objects) == 1
        voice_service = result.voice_objects[0]
        assert isinstance(voice_service, VoiceService)
        return voice_service

    def test_parser_creates_voice_service_object(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        voice_service = self._voice_service(result)

        assert voice_service.object_type == "voice_service"
        assert voice_service.source_parser == "cisco_show_run_voice_service_voip"
        assert voice_service.source_command == "show run | sec voice service voip"
        assert voice_service.source_evidence_id == "EVD-voice-svc-parser"
        assert voice_service.hostname == "cube-edge-01"
        assert voice_service.confidence == result.confidence
        assert voice_service.id.startswith("VOBJ-")

    def test_voice_service_bind_control_extracted(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert voice_service.bind_control == "Loopback0"

    def test_voice_service_bind_media_extracted(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert voice_service.bind_media == "GigabitEthernet0/0/1"

    def test_voice_service_allow_connections_true_when_present(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert voice_service.allow_connections is True

    def test_voice_service_options_ping_true_when_present(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_bindings.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert voice_service.options_ping is True
        assert voice_service.early_offer is True

    def test_disabled_sample_creates_object_and_finding(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_disabled.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        voice_service = self._voice_service(result)

        assert "sip_ua_disabled_by_config" in _signals(result)
        assert voice_service.metadata.get("sip_ua_disabled_by_config") is True
        assert voice_service.allow_connections is None

    def test_supplementary_services_extracted(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert "no supplementary-service sip moved-temporarily" in voice_service.supplementary_services
        assert "no supplementary-service sip refer" in voice_service.supplementary_services

    def test_trusted_ips_extracted_on_voice_service(
        self,
        parser: CiscoShowRunVoiceServiceVoipParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_run_voice_service_voip_normal.txt").read_text(encoding="utf-8")
        voice_service = self._voice_service(parser.parse(raw, parser_context))

        assert voice_service.trusted_ips == ("10.1.1.0 255.255.255.0",)
