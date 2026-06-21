"""Cisco CUCM utils service list parser."""

from __future__ import annotations

import re

from model.cucm_objects import CUCMNode
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'utils service list'
VENDOR = "cisco"
PARSER_ID = 'cisco_utils_service_list'
PARSER_VERSION = "1.0.0"


class CiscoUtilsServiceListParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['service list', 'cisco callmanager', 'cisco tftp', 'show status'])

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

        if structured_data.get("callmanager_stopped"):
            findings.append(ParserFinding(signal="callmanager_service_stopped", confidence=96.0, detail="CallManager service stopped", source_field="callmanager_stopped"))
        elif structured_data.get("callmanager_running"):
            findings.append(ParserFinding(signal="callmanager_service_running", confidence=90.0, detail="CallManager service running", source_field="callmanager_running"))
        if structured_data.get("tftp_stopped"):
            findings.append(ParserFinding(signal="tftp_service_stopped", confidence=94.0, detail="TFTP service stopped", source_field="tftp_stopped"))
        elif structured_data.get("tftp_running"):
            findings.append(ParserFinding(signal="tftp_service_running", confidence=90.0, detail="TFTP service running", source_field="tftp_running"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        node = CUCMNode.create(
            vendor="cisco",
            platform="cucm",
            hostname=context.hostname or "cucm-node",
            source_parser=PARSER_ID,
            source_command=COMMAND,
            source_evidence_id=context.evidence_id or "",
            service_state="stopped" if structured_data.get("callmanager_stopped") else "running",
            metadata={"tftp_stopped": structured_data.get("tftp_stopped", False)},
        )
        return [node]


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        cm_stopped = "cisco callmanager" in lower and any(s in lower for s in ("stopped", "not running", "down"))
        cm_running = "cisco callmanager" in lower and "started" in lower
        tftp_stopped = "cisco tftp" in lower and any(s in lower for s in ("stopped", "not running", "down"))
        tftp_running = "cisco tftp" in lower and "started" in lower
        return {"callmanager_stopped": cm_stopped, "callmanager_running": cm_running, "tftp_stopped": tftp_stopped, "tftp_running": tftp_running}

