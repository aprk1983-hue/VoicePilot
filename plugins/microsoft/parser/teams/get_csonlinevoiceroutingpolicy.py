"""Microsoft Teams ``Get-CsOnlineVoiceRoutingPolicy`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsVoiceRoutingPolicy
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_list_value, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlinevoiceroutingpolicy"
PARSER_ID = "microsoft_get_csonlinevoiceroutingpolicy"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlineVoiceRoutingPolicyParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("onlinvoiceusages", "onlinepstnusages", "voiceroutingpolicy", "pstnusages")
    identity_fields = ("identity",)
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            usages = parse_list_value(record.get("online_pstn_usages") or record.get("pstn_usages"))
            if not usages:
                findings.append(ParserFinding(signal="pstn_usage_missing", confidence=90.0, detail="Voice routing policy has no PSTN usages", source_field="online_pstn_usages"))
                findings.append(ParserFinding(signal="voice_routing_policy_missing", confidence=90.0, detail="Voice routing policy has no PSTN usages", source_field="online_pstn_usages"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity")
            objects.append(
                TeamsVoiceRoutingPolicy.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    route_type=record.get("route_type"),
                    pstn_usages=parse_list_value(record.get("online_pstn_usages") or record.get("pstn_usages")),
                    name=identity or "voice-routing-policy",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
