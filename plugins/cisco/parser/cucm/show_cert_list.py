"""Cisco CUCM show cert list parser."""

from __future__ import annotations

import re

from model.cucm_objects import CUCMNode
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'show cert list'
VENDOR = "cisco"
PARSER_ID = 'cisco_show_cert_list'
PARSER_VERSION = "1.0.0"


class CiscoShowCertListParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['certificate', 'tomcat', 'expir', 'show cert'])

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

        if structured_data.get("certificate_expired"):
            findings.append(ParserFinding(signal="certificate_expired", confidence=93.0, detail="Certificate expired", source_field="certificate_expired"))
            findings.append(ParserFinding(signal="tls_handshake_failed", confidence=85.0, detail="TLS may fail due to certificate", source_field="certificate_expired"))
        elif structured_data.get("certificate_valid"):
            findings.append(ParserFinding(signal="certificate_valid", confidence=90.0, detail="Certificates valid", source_field="certificate_valid"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        return [CUCMNode.create(vendor="cisco", platform="cucm", hostname=context.hostname or "cucm-pub", source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "")]


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        expired = "expired" in lower or "not valid after" in lower and "2020" in lower
        valid = "valid" in lower and "expired" not in lower
        return {"certificate_expired": expired, "certificate_valid": valid and not expired}

