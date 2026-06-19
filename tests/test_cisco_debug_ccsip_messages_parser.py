"""Tests for Cisco debug ccsip messages parser."""

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
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers
from plugins.cisco.parser.debug_ccsip_messages import CiscoDebugCcsipMessagesParser
from runtime.analysis_engine import AnalysisEngine, FINDING_SOURCE_PARSER


@pytest.fixture
def parser() -> CiscoDebugCcsipMessagesParser:
    return CiscoDebugCcsipMessagesParser()


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-cisco-ccsip",
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


@pytest.fixture
def parser_engine(cisco_registry: ParserRegistry) -> ParserEngine:
    return ParserEngine(registry=cisco_registry)


def _signals(result) -> set[str]:
    return {finding.signal for finding in result.findings}


class TestCiscoDebugCcsipMessagesParser:
    def test_detects_sip_trace_sample(self, parser: CiscoDebugCcsipMessagesParser) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        assert parser.detect(raw)

    def test_extracts_503(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert 503 in result.structured_data["response_codes"]
        assert "sip_503_detected" in _signals(result)
        assert result.structured_data["sip_trace_present"] is True

    def test_extracts_404(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_404.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert 404 in result.structured_data["response_codes"]
        assert "sip_404_detected" in _signals(result)

    def test_extracts_488(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_488.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert 488 in result.structured_data["response_codes"]
        assert "sip_488_detected" in _signals(result)

    def test_extracts_call_id(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert "ccsip-503-demo-001@cube-edge-01" in result.structured_data["call_ids"]
        assert "sip_call_id_present" in _signals(result)

    def test_detects_invite(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["has_invite"] is True
        assert "sip_invite_present" in _signals(result)

    def test_detects_bye_and_cancel_when_present(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_488.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["has_bye"] is True
        assert result.structured_data["has_cancel"] is True
        assert "sip_bye_present" in _signals(result)
        assert "sip_cancel_present" in _signals(result)

    def test_returns_structured_data_fields(
        self,
        parser: CiscoDebugCcsipMessagesParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        data = result.structured_data

        assert isinstance(data["sip_trace_present"], bool)
        assert isinstance(data["response_codes"], list)
        assert isinstance(data["response_phrases"], list)
        assert isinstance(data["call_ids"], list)
        assert isinstance(data["from_headers"], list)
        assert isinstance(data["to_headers"], list)
        assert isinstance(data["cseq_methods"], list)
        assert isinstance(data["has_invite"], bool)
        assert isinstance(data["has_bye"], bool)
        assert isinstance(data["has_cancel"], bool)
        assert isinstance(data["has_ack"], bool)

    def test_parser_engine_runs_when_registered(
        self,
        cisco_registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        engine = ParserEngine(registry=cisco_registry)
        result = engine.parse(raw, parser_context, command="debug ccsip messages")

        assert result.command == "debug ccsip messages"
        assert "sip_503_detected" in _signals(result)

    def test_analysis_engine_uses_parser_for_debug_ccsip(
        self,
        cisco_registry: ParserRegistry,
    ) -> None:
        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="CCSIP parser integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        case.status = InvestigationState.ANALYSIS
        case.evidence.append(
            Evidence(
                evidence_id="EVD-ccsip",
                case_id=case.case_id,
                type="cli_output",
                title="CLI paste",
                source=EvidenceSource(
                    origin="cli_paste",
                    collector="engineer",
                    command="debug ccsip messages",
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
        debug_finding = next(f for f in findings if f.signal == "sip_503_detected")

        assert debug_finding.metadata is not None
        assert debug_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert 503 in debug_finding.metadata["structured_data"]["response_codes"]

    def test_detects_minimal_503_line(self, parser: CiscoDebugCcsipMessagesParser) -> None:
        assert parser.detect("SIP/2.0 503 Service Unavailable")
