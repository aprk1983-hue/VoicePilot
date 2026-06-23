"""AudioCodes ``show certificates`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import Certificate
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show certificates"
PARSER_ID = "audiocodes_show_certificates"
PARSER_VERSION = "1.0.0"


class AudioCodesShowCertificatesParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("certificate name", "not after", "certificate status")
    identity_fields = ("certificate_name", "name")
    required_fields = ("certificate_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            status = (record_value(record, "status", "certificate_status") or "").lower()
            if status in {"expired", "invalid"}:
                findings.append(
                    ParserFinding(
                        signal="tls_certificate_expired",
                        confidence=95.0,
                        detail="TLS certificate expired",
                        source_field="status",
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
            certificate_name = record_identity(record, "certificate_name", "name")
            objects.append(
                Certificate.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    certificate_name=certificate_name,
                    not_after=record_value(record, "not_after"),
                    status=record_value(record, "status", "certificate_status"),
                    name=certificate_name or "certificate",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
