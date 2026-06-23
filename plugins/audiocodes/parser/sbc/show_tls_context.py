"""AudioCodes ``show tls-context`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import MediaSecurityProfile, TLSContext
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show tls-context"
PARSER_ID = "audiocodes_show_tls_context"
PARSER_VERSION = "1.0.0"


class AudioCodesShowTlsContextParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("tls context", "certificate name", "tls version")
    identity_fields = ("context_name", "name")
    required_fields = ("context_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            status = (record_value(record, "status", "state") or "").lower()
            if status in {"failed", "error", "negotiation_failed"}:
                findings.append(
                    ParserFinding(
                        signal="tls_negotiation_failure",
                        confidence=92.0,
                        detail="TLS negotiation failure",
                        source_field="status",
                    )
                )
            srtp_mode = (record_value(record, "srtp_mode") or "").lower()
            if srtp_mode in {"disabled", "mismatch"}:
                findings.append(
                    ParserFinding(
                        signal="srtp_mismatch",
                        confidence=90.0,
                        detail="SRTP mode mismatch",
                        source_field="srtp_mode",
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
            context_name = record_identity(record, "context_name", "name")
            if context_name:
                objects.append(
                    TLSContext.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        context_name=context_name,
                        tls_version=record_value(record, "tls_version"),
                        certificate_name=record_value(record, "certificate_name"),
                        name=context_name,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            profile_name = record_value(record, "media_security_profile", "profile_name")
            if profile_name:
                objects.append(
                    MediaSecurityProfile.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        profile_name=profile_name,
                        srtp_mode=record_value(record, "srtp_mode"),
                        name=profile_name,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
        return objects
