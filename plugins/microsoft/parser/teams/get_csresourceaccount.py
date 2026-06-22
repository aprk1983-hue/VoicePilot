"""Microsoft Teams ``Get-CsResourceAccount`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsResourceAccount
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csresourceaccount"
PARSER_ID = "microsoft_get_csresourceaccount"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsResourceAccountParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("resourceaccount", "applicationid", "objectid", "phonenumber")
    identity_fields = ("object_id", "identity", "user_principal_name")
    required_fields = ("object_id",)

    def validate(self, structured_data: JsonDict) -> list[str]:
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in Teams PowerShell evidence"]
        for index, record in enumerate(records):
            if record_identity(record, "object_id", "identity", "user_principal_name") is None:
                errors.append(f"record {index} missing resource account identity")
        return errors

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            if not record.get("phone_number") and not record.get("line_uri"):
                findings.append(ParserFinding(signal="resource_account_missing_license", confidence=88.0, detail="Resource account missing phone number", source_field="phone_number"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "object_id", "identity", "user_principal_name")
            objects.append(
                TeamsResourceAccount.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    application_id=record.get("application_id"),
                    application_type=record.get("application_type"),
                    phone_number=record.get("phone_number") or record.get("line_uri"),
                    name=identity,
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
