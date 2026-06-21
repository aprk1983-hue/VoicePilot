"""Cisco CUCM show risdb query phone parser."""

from __future__ import annotations

import re

from model.cucm_objects import CUCMNode, Phone
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'show risdb query phone'
VENDOR = "cisco"
PARSER_ID = 'cisco_show_risdb'
PARSER_VERSION = "1.0.0"


class CiscoShowRisdbParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['risdb', 'registrations', 'regddevname', 'not registered'])

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

        if structured_data.get("unregistered_count", 0) > 0:
            findings.append(ParserFinding(signal="phone_not_registered", confidence=92.0, detail="Phones not registered", source_field="unregistered_count"))
        if structured_data.get("registered_count", 0) > 0:
            findings.append(ParserFinding(signal="phone_registered", confidence=90.0, detail="Registered phones present", source_field="registered_count"))
        if structured_data.get("ris_unavailable"):
            findings.append(ParserFinding(signal="ris_unavailable", confidence=88.0, detail="RIS data unavailable", source_field="ris_unavailable"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        hostname = context.hostname or "cucm-pub"
        node = CUCMNode.create(vendor="cisco", platform="cucm", hostname=hostname, source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", service_state="active")
        phones = []
        for index in range(structured_data.get("unregistered_count", 0)):
            phones.append(Phone.create(vendor="cisco", platform="cucm", hostname=hostname, source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", name=f"SEP-UNREG-{index+1}", registered=False, cm_node=hostname))
        for index in range(structured_data.get("registered_count", 0)):
            phones.append(Phone.create(vendor="cisco", platform="cucm", hostname=hostname, source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", name=f"SEP-REG-{index+1}", registered=True, cm_node=hostname))
        return [node, *phones]


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        unregistered = len(re.findall(r"not registered|unregistered", lower))
        registered = len(re.findall(r"\bregistered\b", lower))
        ris_unavailable = "ris is not available" in lower or "no registrations" in lower and registered == 0 and unregistered == 0
        return {"unregistered_count": max(unregistered, 1 if "not registered" in lower and registered == 0 else 0), "registered_count": registered, "ris_unavailable": ris_unavailable}

