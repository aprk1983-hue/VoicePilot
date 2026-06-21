"""Cisco CUCM show route plan parser."""

from __future__ import annotations

import re

from model.cucm_objects import RoutePattern, CallingSearchSpace, Partition, RouteList, RouteGroup
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'show route plan'
VENDOR = "cisco"
PARSER_ID = 'cisco_show_route_plan'
PARSER_VERSION = "1.0.0"


class CiscoShowRoutePlanParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['route plan', 'route pattern', 'partition', 'css'])

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

        if structured_data.get("route_pattern_missing"):
            findings.append(ParserFinding(signal="route_pattern_missing", confidence=86.0, detail="Route pattern missing", source_field="route_pattern_missing"))
        if structured_data.get("css_missing"):
            findings.append(ParserFinding(signal="css_missing", confidence=84.0, detail="CSS missing required partition", source_field="css_missing"))
        if structured_data.get("partition_missing"):
            findings.append(ParserFinding(signal="partition_missing", confidence=83.0, detail="Partition missing", source_field="partition_missing"))
        if structured_data.get("route_group_unavailable"):
            findings.append(ParserFinding(signal="route_group_unavailable", confidence=82.0, detail="Route group unavailable", source_field="route_group_unavailable"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        host = context.hostname or "cucm-pub"
        objs = [RoutePattern.create(vendor="cisco", platform="cucm", hostname=host, source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", pattern="9.@")]
        if structured_data.get("css_missing"):
            objs.append(CallingSearchSpace.create(vendor="cisco", platform="cucm", hostname=host, source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or ""))
        return objs


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        return {
            "route_pattern_missing": "no route" in lower or "pattern not found" in lower,
            "css_missing": "css" in lower and ("missing" in lower or "not found" in lower),
            "partition_missing": "partition" in lower and ("missing" in lower or "not found" in lower),
            "route_group_unavailable": "route group" in lower and ("unavailable" in lower or "down" in lower),
        }

