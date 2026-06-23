"""AudioCodes ``show licenses`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import License
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_int, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show licenses"
PARSER_ID = "audiocodes_show_licenses"
PARSER_VERSION = "1.0.0"


class AudioCodesShowLicensesParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("license type", "sessions total", "sessions used")
    identity_fields = ("license_type", "name")
    required_fields = ("license_type", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            total = record_int(record, "sessions_total")
            used = record_int(record, "sessions_used")
            if total is not None and used is not None and used >= total:
                findings.append(
                    ParserFinding(
                        signal="session_license_exhausted",
                        confidence=94.0,
                        detail="Session license exhausted",
                        source_field="sessions_used",
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
            license_type = record_identity(record, "license_type", "name")
            objects.append(
                License.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    license_type=license_type,
                    sessions_total=record_int(record, "sessions_total"),
                    sessions_used=record_int(record, "sessions_used"),
                    name=license_type or "license",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
