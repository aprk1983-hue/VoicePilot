"""Microsoft Teams ``Get-CsCallQueue`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsCallQueue
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_int, parse_list_value, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-cscallqueue"
PARSER_ID = "microsoft_get_cscallqueue"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsCallQueueParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("callqueue", "distributionlists", "agents", "overflowaction")
    identity_fields = ("identity", "name")
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            agents = parse_list_value(record.get("users") or record.get("agents"))
            if not agents:
                findings.append(ParserFinding(signal="call_queue_timeout", confidence=85.0, detail="Call queue has no agents", source_field="users"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity", "name")
            agents = parse_list_value(record.get("users") or record.get("agents"))
            objects.append(
                TeamsCallQueue.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    language_id=record.get("language_id"),
                    distribution_lists=parse_list_value(record.get("distribution_lists")),
                    agents_count=len(agents) if agents else parse_int(record.get("agents_count")),
                    name=identity or "call-queue",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
