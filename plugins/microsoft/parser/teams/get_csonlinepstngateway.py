"""Microsoft Teams ``Get-CsOnlinePSTNGateway`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsPstnGateway
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_bool, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlinepstngateway"
PARSER_ID = "microsoft_get_csonlinepstngateway"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlinePstnGatewayParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("fqdn", "pstngateway", "forwardcallhistory", "enabled")
    identity_fields = ("identity",)
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            enabled = parse_bool(record.get("enabled"))
            if enabled is False:
                findings.append(ParserFinding(signal="direct_routing_sbc_unreachable", confidence=92.0, detail="PSTN gateway disabled", source_field="enabled"))
            if not record.get("fqdn"):
                findings.append(ParserFinding(signal="sbc_connectivity_lost", confidence=88.0, detail="PSTN gateway missing FQDN", source_field="fqdn"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity")
            objects.append(
                TeamsPstnGateway.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    fqdn=record.get("fqdn"),
                    enabled=parse_bool(record.get("enabled")),
                    forward_call_history=parse_bool(record.get("forward_call_history")),
                    name=identity or "pstn-gateway",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
