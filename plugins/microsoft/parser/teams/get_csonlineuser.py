"""Microsoft Teams ``Get-CsOnlineUser`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsUser
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_bool, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlineuser"
PARSER_ID = "microsoft_get_csonlineuser"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlineUserParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("enterprisevoiceenabled", "userprincipalname", "lineuri", "onpremlineuri")
    identity_fields = ("user_principal_name", "identity")
    required_fields = ("user_principal_name",)

    def validate(self, structured_data: JsonDict) -> list[str]:
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in Teams PowerShell evidence"]
        for index, record in enumerate(records):
            if record_identity(record, "user_principal_name", "identity") is None:
                errors.append(f"record {index} missing user identity")
        return errors

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            enabled = parse_bool(record.get("enterprise_voice_enabled"))
            if enabled is True:
                findings.append(ParserFinding(signal="enterprise_voice_enabled", confidence=95.0, detail="Enterprise Voice enabled", source_field="enterprise_voice_enabled"))
            elif enabled is False:
                findings.append(ParserFinding(signal="enterprise_voice_disabled", confidence=95.0, detail="Enterprise Voice disabled", source_field="enterprise_voice_enabled"))
            license_assigned = parse_bool(
                record.get("teams_phone_license_assigned")
                or record.get("teams_phone_system_license")
            )
            if license_assigned is False:
                findings.append(
                    ParserFinding(
                        signal="teams_phone_license_missing",
                        confidence=92.0,
                        detail="Teams Phone license not assigned",
                        source_field="teams_phone_license_assigned",
                    )
                )
            if not record.get("online_voice_routing_policy") and not record.get("voice_routing_policy"):
                findings.append(ParserFinding(signal="voice_routing_policy_missing", confidence=88.0, detail="No voice routing policy assigned", source_field="online_voice_routing_policy"))
            if not record.get("line_uri") and not record.get("on_prem_line_uri"):
                findings.append(ParserFinding(signal="phone_number_assignment_failed", confidence=85.0, detail="No LineUri assigned", source_field="line_uri"))
            if not record.get("emergency_calling_policy") and not record.get("online_emergency_calling_policy"):
                findings.append(
                    ParserFinding(
                        signal="emergency_calling_policy_missing",
                        confidence=90.0,
                        detail="No emergency calling policy assigned",
                        source_field="emergency_calling_policy",
                    )
                )
            if not record.get("emergency_routing_policy") and not record.get("online_emergency_routing_policy"):
                findings.append(
                    ParserFinding(
                        signal="emergency_routing_policy_missing",
                        confidence=88.0,
                        detail="No emergency routing policy assigned",
                        source_field="emergency_routing_policy",
                    )
                )
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            upn = record_identity(record, "user_principal_name", "identity")
            objects.append(
                TeamsUser.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    user_principal_name=upn,
                    enterprise_voice_enabled=parse_bool(record.get("enterprise_voice_enabled")),
                    line_uri=record.get("line_uri") or record.get("on_prem_line_uri"),
                    voice_routing_policy=record.get("online_voice_routing_policy") or record.get("voice_routing_policy"),
                    dial_plan=record.get("tenant_dialplan") or record.get("dial_plan"),
                    name=upn,
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
