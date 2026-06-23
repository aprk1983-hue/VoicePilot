"""AudioCodes ``show routing-table`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import RoutingRule
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_int, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show routing-table"
PARSER_ID = "audiocodes_show_routing_table"
PARSER_VERSION = "1.0.0"


class AudioCodesShowRoutingTableParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("routing table", "destination", "ip group")
    identity_fields = ("rule_name", "name")
    required_fields = ("rule_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            if not record_value(record, "ip_group", "destination"):
                findings.append(
                    ParserFinding(
                        signal="routing_table_issue",
                        confidence=91.0,
                        detail="Routing table entry missing destination or IP Group",
                        source_field="ip_group",
                    )
                )
        return findings

    def extract_voice_objects(
        self,
        structured_data: JsonDict,
        context: ParserContext,
        *,
        confidence: float,
    ) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            rule_name = record_identity(record, "rule_name", "name")
            objects.append(
                RoutingRule.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    rule_name=rule_name,
                    destination=record_value(record, "destination"),
                    ip_group=record_value(record, "ip_group"),
                    priority=record_int(record, "priority"),
                    name=rule_name or "routing-rule",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
