"""Skeleton tests for the parser framework architecture."""

from __future__ import annotations

import pytest

from parser.command_detector import KNOWN_COMMANDS, CommandDetector
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_exceptions import (
    CommandDetectionError,
    ParserAlreadyRegisteredError,
    ParserNotFoundError,
    ParserValidationError,
    VoicePilotParserError,
)
from parser.parser_registry import ParserRegistry
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict


class StubParser(CommandParser):
    """Minimal parser stub for framework tests."""

    vendor = "cisco"
    command = "show sip-ua status"
    parser_version = "0.0.0-skeleton"

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        return "sip-ua" in raw_text.lower()

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        structured = {"raw_length": len(raw_text)}
        errors = self.validate(structured)
        return ParserResult(
            command=self.command,
            hostname=context.hostname,
            platform=context.platform,
            ios_version=context.ios_version,
            parser_version=self.parser_version,
            errors=errors,
            metadata=self.extract_metadata(structured, context),
            structured_data=structured,
            findings=self.extract_findings(structured, context),
            confidence=100.0 if not errors else 0.0,
        )

    def validate(self, structured_data: JsonDict) -> list[str]:
        if structured_data.get("raw_length", 0) == 0:
            return ["empty output"]
        return []

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        return [
            ParserFinding(
                signal="stub_finding",
                confidence=50.0,
                detail="skeleton finding",
            )
        ]

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        return {"vendor": context.vendor, "case_id": context.case_id}


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-test",
        device_id="DEV-test",
        platform="CUBE",
        ios_version="17.9.1",
        hostname="cube-edge-01",
    )


@pytest.fixture
def registry() -> ParserRegistry:
    reg = ParserRegistry()
    reg.register(StubParser())
    yield reg
    reg.clear()


class TestParserContext:
    def test_context_exposes_required_fields(self, parser_context: ParserContext) -> None:
        assert parser_context.vendor == "cisco"
        assert parser_context.case_id == "CASE-test"
        assert parser_context.device_id == "DEV-test"
        assert parser_context.platform == "CUBE"
        assert parser_context.ios_version == "17.9.1"
        assert parser_context.hostname == "cube-edge-01"
        assert parser_context.timezone == "UTC"
        assert parser_context.collection_timestamp is not None


class TestParserResult:
    def test_result_fields_and_validity(self) -> None:
        result = ParserResult(
            command="show sip-ua status",
            hostname="cube-edge-01",
            platform="CUBE",
            ios_version="17.9.1",
            parser_version="0.0.0-skeleton",
            warnings=["partial output"],
            metadata={"vendor": "cisco"},
            structured_data={"status": "disabled"},
            findings=[ParserFinding(signal="sip_ua_disabled", confidence=90.0)],
            confidence=90.0,
        )

        assert result.command == "show sip-ua status"
        assert result.is_valid
        assert result.findings[0].signal == "sip_ua_disabled"

    def test_result_invalid_when_errors_present(self) -> None:
        result = ParserResult(command="show version", errors=["parse failed"])
        assert not result.is_valid


class TestParserRegistry:
    def test_register_and_lookup_parser(self, registry: ParserRegistry) -> None:
        parser = registry.get_parser("cisco", "show sip-ua status")
        assert isinstance(parser, CommandParser)
        assert parser.vendor == "cisco"

    def test_lookup_missing_parser_raises(self, registry: ParserRegistry) -> None:
        with pytest.raises(ParserNotFoundError):
            registry.get_parser("cisco", "show version")

    def test_duplicate_registration_raises(self, registry: ParserRegistry) -> None:
        with pytest.raises(ParserAlreadyRegisteredError):
            registry.register(StubParser())

    def test_list_vendors_and_commands(self, registry: ParserRegistry) -> None:
        assert registry.list_vendors() == ("cisco",)
        assert "show sip-ua status" in registry.list_commands("cisco")


class TestCommandDetector:
    def test_known_commands_catalog(self) -> None:
        detector = CommandDetector()
        assert "show sip-ua status" in detector.known_commands
        assert "debug ccsip messages" in KNOWN_COMMANDS

    def test_normalize_command(self) -> None:
        detector = CommandDetector()
        assert detector.normalize_command("  SHOW   sip-ua   status  ") == "show sip-ua status"

    def test_detect_returns_none_in_architecture_sprint(self) -> None:
        detector = CommandDetector()
        assert detector.detect("SIP-UA Status: disabled") is None


class TestParserEngine:
    def test_parse_with_explicit_command(
        self,
        registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        engine = ParserEngine(registry=registry)
        result = engine.parse(
            "SIP-UA Status: disabled",
            parser_context,
            command="show sip-ua status",
        )

        assert result.command == "show sip-ua status"
        assert result.parser_version == "0.0.0-skeleton"
        assert result.findings
        assert result.is_valid

    def test_parse_without_command_raises_when_detection_unimplemented(
        self,
        registry: ParserRegistry,
        parser_context: ParserContext,
    ) -> None:
        engine = ParserEngine(registry=registry)
        with pytest.raises(CommandDetectionError):
            engine.parse("SIP-UA Status: disabled", parser_context)

    def test_parse_missing_parser_raises(self, parser_context: ParserContext) -> None:
        engine = ParserEngine(registry=ParserRegistry())
        with pytest.raises(ParserNotFoundError):
            engine.parse("output", parser_context, command="show version")


class TestParserExceptions:
    def test_exception_hierarchy(self) -> None:
        assert issubclass(ParserNotFoundError, VoicePilotParserError)
        assert issubclass(ParserValidationError, VoicePilotParserError)

    def test_parser_not_found_message(self) -> None:
        exc = ParserNotFoundError("cisco", "show version")
        assert exc.vendor == "cisco"
        assert exc.command == "show version"
