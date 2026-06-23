"""AudioCodes ``show sip-options`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import SIPMessagePolicy
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_bool, record_identity, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show sip-options"
PARSER_ID = "audiocodes_show_sip_options"
PARSER_VERSION = "1.0.0"


class AudioCodesShowSipOptionsParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("sip options", "options enabled", "keepalive")
    identity_fields = ("policy_name", "name")
    required_fields = ("policy_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            options_status = (record_value(record, "options_status", "status") or "").lower()
            options_enabled = record_bool(record, "options_enabled")
            if options_enabled is False or options_status in {"failed", "failure", "timeout"}:
                findings.append(
                    ParserFinding(
                        signal="sip_options_failure",
                        confidence=93.0,
                        detail="SIP OPTIONS failure",
                        source_field="options_status",
                    )
                )
            if options_status == "503":
                findings.append(
                    ParserFinding(
                        signal="provider_503",
                        confidence=90.0,
                        detail="Provider returned SIP 503",
                        source_field="options_status",
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
            policy_name = record_identity(record, "policy_name", "name")
            objects.append(
                SIPMessagePolicy.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    policy_name=policy_name,
                    options_enabled=record_bool(record, "options_enabled"),
                    name=policy_name or "sip-message-policy",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
