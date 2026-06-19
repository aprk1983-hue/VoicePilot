"""Tests for Cisco show sip-ua status parser."""

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

from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers
from plugins.cisco.parser.show_sip_ua_status import CiscoShowSipUaStatusParser


@pytest.fixture
def parser() -> CiscoShowSipUaStatusParser:
    return CiscoShowSipUaStatusParser()


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-cisco-parser",
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


class TestCiscoShowSipUaStatusParser:
    def test_detects_enabled_sample(self, parser: CiscoShowSipUaStatusParser) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_enabled.txt").read_text(encoding="utf-8")
        assert parser.detect(raw)

    def test_detects_disabled_sample(self, parser: CiscoShowSipUaStatusParser) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        assert parser.detect(raw)

    def test_detects_sip_ua_enabled_output(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_enabled.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["sip_ua_enabled"] is True
        assert "sip_ua_enabled" in _signals(result)
        assert "sip_ua_disabled" not in _signals(result)
        assert result.structured_data["registration_state"] == "registered"
        assert "sip_registration_present" in _signals(result)

    def test_detects_sip_ua_disabled_output(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["sip_ua_enabled"] is False
        assert "sip_ua_disabled" in _signals(result)
        assert result.is_valid

    def test_detects_registered_state(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_registered_tls.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["registration_state"] == "registered"
        assert "sip_registration_present" in _signals(result)

    def test_detects_unregistered_state(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = """SIP-UA Status: enabled
 Registrar Host: sip:provider.example.com
 SIP Trunk Status: unregistered
"""
        result = parser.parse(raw, parser_context)

        assert result.structured_data["registration_state"] == "unregistered"
        assert "sip_registration_issue" in _signals(result)

    def test_detects_failed_registration(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = """SIP-UA Status: enabled
 Registrar: sip:provider.example.com
 Registration: failed
"""
        result = parser.parse(raw, parser_context)

        assert result.structured_data["registration_state"] == "failed"
        assert "sip_registration_issue" in _signals(result)

    def test_detects_tls_transport(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_registered_tls.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.structured_data["transport"] == "tls"
        assert "sip_transport_tls_detected" in _signals(result)

    def test_returns_structured_data_fields(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_registered_tls.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)
        data = result.structured_data

        assert "sip_ua_enabled" in data
        assert "registration_state" in data
        assert "registrar_present" in data
        assert "registrar_host" in data
        assert "transport" in data
        assert "raw_status_lines" in data
        assert data["registrar_present"] is True
        assert data["registrar_host"] == "sip:pstn.carrier.com"
        assert isinstance(data["raw_status_lines"], list)
        assert len(data["raw_status_lines"]) >= 3

    def test_returns_findings_and_metadata(
        self,
        parser: CiscoShowSipUaStatusParser,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_enabled.txt").read_text(encoding="utf-8")
        result = parser.parse(raw, parser_context)

        assert result.findings
        assert result.metadata["vendor"] == "cisco"
        assert result.metadata["command"] == "show sip-ua status"
        assert result.parser_version == "1.0.0"
        assert result.hostname == "cube-edge-01"

    def test_parser_engine_runs_when_registered(
        self,
        cisco_registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        raw = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        engine = ParserEngine(registry=cisco_registry)
        result = engine.parse(raw, parser_context, command="show sip-ua status")

        assert result.command == "show sip-ua status"
        assert result.structured_data["sip_ua_enabled"] is False
        assert "sip_ua_disabled" in _signals(result)

    def test_validate_reports_empty_output(self, parser: CiscoShowSipUaStatusParser) -> None:
        errors = parser.validate({"raw_status_lines": []})
        assert errors
