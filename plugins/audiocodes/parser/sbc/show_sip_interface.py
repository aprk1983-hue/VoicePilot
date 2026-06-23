"""AudioCodes ``show sip-interface`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import SIPInterface
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_int, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show sip-interface"
PARSER_ID = "audiocodes_show_sip_interface"
PARSER_VERSION = "1.0.0"


class AudioCodesShowSipInterfaceParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("sip interface", "interface name", "transport")
    identity_fields = ("interface_name", "name")
    required_fields = ("interface_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            state = (record_value(record, "state", "status") or "").lower()
            if state in {"down", "disabled", "inactive"}:
                findings.append(
                    ParserFinding(
                        signal="sip_interface_down",
                        confidence=93.0,
                        detail="SIP Interface is down",
                        source_field="state",
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
            identity = record_identity(record, "interface_name", "name")
            objects.append(
                SIPInterface.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    interface_name=identity,
                    state=record_value(record, "state", "status"),
                    transport=record_value(record, "transport"),
                    port=record_int(record, "port"),
                    tls_context=record_value(record, "tls_context"),
                    media_realm=record_value(record, "media_realm"),
                    name=identity or "sip-interface",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
