"""Microsoft Teams ``Get-CsAutoAttendant`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsAutoAttendant
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csautoattendant"
PARSER_ID = "microsoft_get_csautoattendant"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsAutoAttendantParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("autoattendant", "operator", "timezoneid", "defaultcallflow")
    identity_fields = ("identity", "name")
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            if not record.get("operator") and not record.get("default_call_flow"):
                findings.append(ParserFinding(signal="auto_attendant_transfer_failure", confidence=85.0, detail="Auto attendant missing operator/call flow", source_field="operator"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity", "name")
            objects.append(
                TeamsAutoAttendant.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    language_id=record.get("language_id"),
                    time_zone_id=record.get("time_zone_id"),
                    operator=record.get("operator"),
                    name=identity or "auto-attendant",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
