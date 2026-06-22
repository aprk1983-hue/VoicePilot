"""Microsoft Teams ``Get-CsOnlineVoiceRoute`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsVoiceRoute
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_int, parse_list_value, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlinevoiceroute"
PARSER_ID = "microsoft_get_csonlinevoiceroute"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlineVoiceRouteParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("numberpattern", "onlinepstngatewaylist", "onlinepstnusages", "voiceroute")
    identity_fields = ("identity",)
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            gateways = parse_list_value(record.get("online_pstn_gateway_list"))
            if not gateways:
                findings.append(ParserFinding(signal="voice_routing_failure_pstn", confidence=88.0, detail="Voice route has no PSTN gateway", source_field="online_pstn_gateway_list"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity")
            objects.append(
                TeamsVoiceRoute.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    number_pattern=record.get("number_pattern"),
                    online_pstn_gateway_list=parse_list_value(record.get("online_pstn_gateway_list")),
                    online_pstn_usages=parse_list_value(record.get("online_pstn_usages")),
                    priority=parse_int(record.get("priority")),
                    name=identity or "voice-route",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
