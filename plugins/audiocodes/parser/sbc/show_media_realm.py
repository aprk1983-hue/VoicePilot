"""AudioCodes ``show media-realm`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import MediaRealm
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_identity, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show media-realm"
PARSER_ID = "audiocodes_show_media_realm"
PARSER_VERSION = "1.0.0"


class AudioCodesShowMediaRealmParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("media realm", "port range", "realm name")
    identity_fields = ("realm_name", "name")
    required_fields = ("realm_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            state = (record_value(record, "state", "status") or "").lower()
            if state in {"failed", "down", "inactive"}:
                findings.append(
                    ParserFinding(
                        signal="media_realm_failure",
                        confidence=92.0,
                        detail="Media Realm failure",
                        source_field="state",
                    )
                )
            if not record_value(record, "ip_address", "media_ip"):
                findings.append(
                    ParserFinding(
                        signal="rtp_one_way_audio",
                        confidence=88.0,
                        detail="Media Realm missing media IP",
                        source_field="ip_address",
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
            realm_name = record_identity(record, "realm_name", "name")
            objects.append(
                MediaRealm.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=sbc_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    realm_name=realm_name,
                    state=record_value(record, "state", "status"),
                    ip_address=record_value(record, "ip_address", "media_ip"),
                    port_range=record_value(record, "port_range"),
                    name=realm_name or "media-realm",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
