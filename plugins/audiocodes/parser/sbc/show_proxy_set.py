"""AudioCodes ``show proxy-set`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import ProxyAddress, ProxySet
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import (
    PLATFORM,
    VENDOR,
    record_bool,
    record_identity,
    record_int,
    record_value,
    sbc_hostname,
)
from shared.types import JsonDict

COMMAND = "show proxy-set"
PARSER_ID = "audiocodes_show_proxy_set"
PARSER_VERSION = "1.0.0"


class AudioCodesShowProxySetParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("proxy set", "proxy address", "enable heartbeat")
    identity_fields = ("proxy_set_name", "name")
    required_fields = ("proxy_set_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "down", "inactive"}:
                findings.append(
                    ParserFinding(
                        signal="proxy_set_unavailable",
                        confidence=92.0,
                        detail="Proxy Set unavailable",
                        source_field="state",
                    )
                )
            if not record_value(record, "address", "proxy_address"):
                findings.append(
                    ParserFinding(
                        signal="gateway_unreachable",
                        confidence=88.0,
                        detail="Proxy Set missing gateway address",
                        source_field="address",
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
        hostname = sbc_hostname(context)
        for record in self._records(structured_data):
            proxy_set_name = record_identity(record, "proxy_set_name", "name")
            if proxy_set_name:
                objects.append(
                    ProxySet.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        proxy_set_name=proxy_set_name,
                        state=record_value(record, "state", "status"),
                        enable_heartbeat=record_bool(record, "enable_heartbeat"),
                        name=proxy_set_name,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            address = record_value(record, "address", "proxy_address")
            if address:
                objects.append(
                    ProxyAddress.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        proxy_set_name=proxy_set_name,
                        address=address,
                        transport=record_value(record, "transport"),
                        port=record_int(record, "port"),
                        name=address,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
        return objects
