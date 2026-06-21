"""Cisco CUCM show sip trunk parser."""

from __future__ import annotations

import re

from model.cucm_objects import SIPTrunk
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'show sip trunk'
VENDOR = "cisco"
PARSER_ID = 'cisco_show_sip_trunk'
PARSER_VERSION = "1.0.0"


class CiscoShowSipTrunkParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['sip trunk', 'trunk status', 'sip trunk status'])

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        structured = self._build_structured_data(raw_text)
        errors = self.validate(structured)
        findings = self.extract_findings(structured, context) if not errors else []
        voice_objects = self.extract_voice_objects(structured, context) if not errors else []
        return ParserResult(
            command=self.command,
            hostname=context.hostname,
            platform=context.platform,
            ios_version=context.ios_version,
            parser_version=self.parser_version,
            warnings=[],
            errors=errors,
            metadata={"command": self.command},
            structured_data=structured,
            findings=findings,
            voice_objects=voice_objects,
            confidence=90.0 if not errors else 0.0,
        )

    def validate(self, structured_data: JsonDict) -> list[str]:
        return []

    def extract_metadata(self, structured_data: JsonDict, context: ParserContext) -> JsonDict:
        return default_cucm_metadata(self, structured_data, context)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []

        if structured_data.get("trunk_down"):
            findings.append(ParserFinding(signal="sip_trunk_down", confidence=91.0, detail="SIP trunk down", source_field="trunk_down"))
        elif structured_data.get("trunk_up"):
            findings.append(ParserFinding(signal="sip_trunk_up", confidence=90.0, detail="SIP trunk up", source_field="trunk_up"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        status = "Down" if structured_data.get("trunk_down") else "Up"
        return [SIPTrunk.create(vendor="cisco", platform="cucm", hostname=context.hostname or "cucm-pub", source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", status=status, name="ITSP-TRUNK")]


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        down = any(token in lower for token in ("status: down", "state: down", "not in service", "unavailable"))
        up = "status: up" in lower or "in service" in lower
        return {"trunk_down": down, "trunk_up": up and not down}

