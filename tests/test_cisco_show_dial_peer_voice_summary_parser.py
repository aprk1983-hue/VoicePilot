"""Tests for Cisco show dial-peer voice summary parser."""

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
from model.dial_peer import DialPeer
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers
from plugins.cisco.parser.show_dial_peer_voice_summary import CiscoShowDialPeerVoiceSummaryParser
from runtime.analysis_engine import AnalysisEngine, FINDING_SOURCE_PARSER


@pytest.fixture
def parser() -> CiscoShowDialPeerVoiceSummaryParser:
    return CiscoShowDialPeerVoiceSummaryParser()


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-cisco-dial-peer",
        evidence_id="EVD-dial-peer-parser",
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


class TestCiscoShowDialPeerVoiceSummaryParser:
    def test_detects_command_output(self, parser: CiscoShowDialPeerVoiceSummaryParser) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        assert parser.detect(raw)

    def test_detects_normal_dial_peers(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["dial_peer_summary_present"] is True
        assert result.structured_data["dial_peer_count"] == 2
        assert "dial_peer_summary_present" in _signals(result)
        assert "dial_peer_config_present" in _signals(result)

    def test_counts_voip_dial_peers(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["voip_dial_peer_count"] == 2
        assert result.structured_data["pots_dial_peer_count"] == 0

    def test_detects_empty_or_missing_output(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_empty.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["dial_peer_summary_missing_or_empty"] is True
        assert result.structured_data["dial_peer_count"] == 0
        assert "dial_peer_summary_missing_or_empty" in _signals(result)

    def test_detects_down_and_out_of_service(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_down.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["down_dial_peer_count"] == 1
        assert result.structured_data["out_of_service_count"] == 1
        assert "dial_peer_down" in _signals(result)
        assert "dial_peer_out_of_service" in _signals(result)

    def test_extracts_destination_patterns(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert "9T" in result.structured_data["destination_patterns"]
        assert "8011" in result.structured_data["destination_patterns"]
        assert "outbound_dial_peer_candidates_present" in _signals(result)

    def test_extracts_session_targets(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert "ipv4:192.0.2.10" in result.structured_data["session_targets"]
        assert "session_target_present" in _signals(result)

    def test_returns_structured_data_fields(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        data = parser.parse(raw, parser_context).structured_data

        assert isinstance(data["raw_dial_peer_lines"], list)
        assert len(data["raw_dial_peer_lines"]) >= 4

    def test_parser_engine_runs_when_registered(
        self,
        cisco_registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        engine = ParserEngine(registry=cisco_registry)
        result = engine.parse(raw, parser_context, command="show dial-peer voice summary")

        assert result.command == "show dial-peer voice summary"
        assert result.structured_data["dial_peer_count"] == 2

    def test_analysis_engine_uses_parser_for_dial_peer_summary(
        self,
        cisco_registry: ParserRegistry,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Dial-peer parser integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        case.status = InvestigationState.ANALYSIS
        case.evidence.append(
            Evidence(
                evidence_id="EVD-dial-peer",
                case_id=case.case_id,
                type="cli_output",
                title="CLI paste",
                source=EvidenceSource(
                    origin="cli_paste",
                    collector="engineer",
                    command="show dial-peer voice summary",
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
        dial_peer_finding = next(f for f in findings if f.signal == "dial_peer_config_present")

        assert dial_peer_finding.metadata is not None
        assert dial_peer_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert dial_peer_finding.metadata["structured_data"]["voip_dial_peer_count"] == 2
        assert "related_voice_object_ids" in dial_peer_finding.metadata
        assert len(dial_peer_finding.metadata["related_voice_object_ids"]) == 2


class TestCiscoShowDialPeerVoiceSummaryParserCvom:
    def test_parser_creates_dial_peer_objects(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert len(result.voice_objects) == 2
        assert all(isinstance(obj, DialPeer) for obj in result.voice_objects)

    def test_normal_sample_creates_two_dial_peer_objects(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["parsed_dial_peers"]
        assert len(result.structured_data["parsed_dial_peers"]) == 2
        assert len(result.voice_objects) == 2

    def test_dial_peer_tags_extracted(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        tags = {str(peer.tag) for peer in result.voice_objects}

        assert tags == {"1", "2"}

    def test_destination_patterns_extracted(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        patterns = {peer.destination_pattern for peer in result.voice_objects}

        assert patterns == {"9T", "8011"}

    def test_session_targets_extracted(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        targets = {peer.session_target for peer in result.voice_objects}

        assert targets == {"ipv4:192.0.2.10", "ipv4:198.51.100.20"}

    def test_down_out_of_service_sample_maps_status(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_down.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        by_tag = {str(peer.tag): peer for peer in result.voice_objects}

        assert by_tag["1"].status == "down"
        assert by_tag["1"].shutdown is True
        assert by_tag["2"].status == "out_of_service"
        assert by_tag["2"].shutdown is True

    def test_voice_object_provenance(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        peer = result.voice_objects[0]

        assert peer.source_parser == "cisco_show_dial_peer_voice_summary"
        assert peer.source_command == "show dial-peer voice summary"
        assert peer.source_evidence_id == "EVD-dial-peer-parser"
        assert peer.peer_type == "voip"
        assert peer.id.startswith("VOBJ-")

    def test_empty_sample_has_no_voice_objects(
        self,
        parser: CiscoShowDialPeerVoiceSummaryParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_empty.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.voice_objects == []
