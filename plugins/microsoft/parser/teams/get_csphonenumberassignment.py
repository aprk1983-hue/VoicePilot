"""Microsoft Teams ``Get-CsPhoneNumberAssignment`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsPhoneNumber
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csphonenumberassignment"
PARSER_ID = "microsoft_get_csphonenumberassignment"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsPhoneNumberAssignmentParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("telephonenumber", "assignedpii", "assignmentcategory", "phonenumber")
    identity_fields = ("telephone_number", "phone_number")
    required_fields = ("telephone_number",)

    def validate(self, structured_data: JsonDict) -> list[str]:
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in Teams PowerShell evidence"]
        for index, record in enumerate(records):
            if record_identity(record, "telephone_number", "phone_number") is None:
                errors.append(f"record {index} missing telephone number")
        return errors

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            status = str(record.get("assignment_status") or record.get("number_type") or "").lower()
            if status and "unassigned" in status:
                findings.append(ParserFinding(signal="phone_number_assignment_failed", confidence=90.0, detail="Phone number unassigned", source_field="assignment_status"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            number = record_identity(record, "telephone_number", "phone_number")
            objects.append(
                TeamsPhoneNumber.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    telephone_number=number,
                    assigned_purpose=record.get("assigned_purpose") or record.get("assignment_category"),
                    assignment_status=record.get("assignment_status") or record.get("number_type"),
                    assigned_to=record.get("assigned_to") or record.get("pii"),
                    name=number,
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
