"""AudioCodes ``show voip status`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import SBCDevice
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show voip status"
PARSER_ID = "audiocodes_show_voip_status"
PARSER_VERSION = "1.0.0"


class AudioCodesShowVoipStatusParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("voip status", "active sessions", "device status")
    identity_fields = ("device_name", "name")
    required_fields = ("device_name", "name")

    def validate(self, structured_data: JsonDict) -> list[str]:
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in AudioCodes SBC evidence"]
        if not any(record.get("device_name") or record.get("name") for record in records):
            return ["voip status evidence missing device identity"]
        return []

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            dns_status = (record_value(record, "dns_resolution") or "").lower()
            if dns_status in {"failed", "failure"}:
                findings.append(
                    ParserFinding(
                        signal="dns_resolution_failure",
                        confidence=86.0,
                        detail="DNS resolution failure",
                        source_field="dns_resolution",
                    )
                )
            call_failures = (record_value(record, "call_failures") or "").lower()
            if call_failures in {"elevated", "high", "spike"}:
                findings.append(
                    ParserFinding(
                        signal="call_failure_spike",
                        confidence=85.0,
                        detail="Elevated call failure rate",
                        source_field="call_failures",
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
        record = self._records(structured_data)[0]
        return [
            SBCDevice.create(
                vendor=context.vendor,
                platform=context.platform or PLATFORM,
                hostname=sbc_hostname(context),
                source_parser=PARSER_ID,
                source_command=self.command,
                source_evidence_id=context.evidence_id or "",
                device_name=record_value(record, "device_name", "name"),
                device_status=record_value(record, "device_status", "status"),
                confidence=confidence,
                metadata=dict(record),
            )
        ]
