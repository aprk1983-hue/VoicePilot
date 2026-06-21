"""Cisco CUCM utils dbreplication runtimestate parser."""

from __future__ import annotations

import re

from model.cucm_objects import CUCMCluster, CUCMNode
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.cisco.parser.cucm._helpers import default_cucm_metadata
from shared.types import JsonDict

COMMAND = 'utils dbreplication runtimestate'
VENDOR = "cisco"
PARSER_ID = 'cisco_utils_dbreplication'
PARSER_VERSION = "1.0.0"


class CiscoUtilsDbReplicationParser(CommandParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        return any(marker in lower for marker in ['dbreplication', 'replication', 'runtimestate'])

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

        if structured_data.get("replication_healthy") is False:
            findings.append(ParserFinding(signal="db_replication_unhealthy", confidence=95.0, detail="DB replication unhealthy", source_field="replication_healthy"))
        elif structured_data.get("replication_healthy"):
            findings.append(ParserFinding(signal="db_replication_healthy", confidence=90.0, detail="DB replication healthy", source_field="replication_healthy"))

        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext) -> list:

        cluster = CUCMCluster.create(vendor="cisco", platform="cucm", hostname=context.hostname or "cucm-cluster", source_parser=PARSER_ID, source_command=COMMAND, source_evidence_id=context.evidence_id or "", publisher=context.hostname or "cucm-pub", node_count=2)
        node = CUCMNode.create(
            vendor="cisco",
            platform="cucm",
            hostname=context.hostname or "cucm-pub",
            source_parser=PARSER_ID,
            source_command=COMMAND,
            source_evidence_id=context.evidence_id or "",
            metadata={"replication_healthy": structured_data.get("replication_healthy")},
        )
        return [cluster, node]


    def _build_structured_data(self, raw_text: str) -> JsonDict:
        lower = raw_text.lower()

        unhealthy = any(token in lower for token in ("state = 0", "not connected", "mismatch", "broken", "error"))
        healthy = "state = 2" in lower or "normal" in lower
        return {"replication_healthy": False if unhealthy else True if healthy else None}

