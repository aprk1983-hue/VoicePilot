"""Microsoft Teams ``Get-CsOnlineLisLocation`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsLisLocation
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_bool, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlinelislocation"
PARSER_ID = "microsoft_get_csonlinelislocation"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlineLisLocationParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("lislocation", "civicaddress", "locationid", "e911")
    identity_fields = ("location_id", "identity")
    required_fields = ("location_id",)

    def validate(self, structured_data: JsonDict) -> list[str]:
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in Teams PowerShell evidence"]
        for index, record in enumerate(records):
            if record_identity(record, "location_id", "identity") is None:
                errors.append(f"record {index} missing location identity")
        return errors

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            if not record.get("civic_address") and not record.get("location"):
                findings.append(ParserFinding(signal="emergency_calling_policy_missing", confidence=90.0, detail="LIS location missing civic address", source_field="civic_address"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "location_id", "identity")
            objects.append(
                TeamsLisLocation.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    civic_address=record.get("civic_address"),
                    location=record.get("location") or record.get("description"),
                    e911_enabled=parse_bool(record.get("e911_enabled")),
                    name=identity or "lis-location",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
