"""AudioCodes ``show ip-group`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import IPGroup, IPProfile
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import (
    PLATFORM,
    VENDOR,
    record_bool,
    record_identity,
    record_value,
    sbc_hostname,
)
from shared.types import JsonDict

COMMAND = "show ip-group"
PARSER_ID = "audiocodes_show_ip_group"
PARSER_VERSION = "1.0.0"


class AudioCodesShowIpGroupParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("ip group", "proxy set", "media realm", "ip profile")
    identity_fields = ("ip_group_name", "name")
    required_fields = ("ip_group_name", "name")

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            state = (record_value(record, "state", "status") or "").lower()
            if state in {"disabled", "inactive", "down"}:
                findings.append(
                    ParserFinding(
                        signal="ip_group_disabled",
                        confidence=93.0,
                        detail="IP Group disabled",
                        source_field="state",
                    )
                )
            proxy_set = record_value(record, "proxy_set")
            configured_proxy = record_value(record, "expected_proxy_set")
            if proxy_set and configured_proxy and proxy_set != configured_proxy:
                findings.append(
                    ParserFinding(
                        signal="ip_group_mismatch",
                        confidence=90.0,
                        detail="IP Group proxy set mismatch",
                        source_field="proxy_set",
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
            ip_group_name = record_identity(record, "ip_group_name", "name")
            if ip_group_name:
                objects.append(
                    IPGroup.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        ip_group_name=ip_group_name,
                        state=record_value(record, "state", "status"),
                        proxy_set=record_value(record, "proxy_set"),
                        media_realm=record_value(record, "media_realm"),
                        ip_profile=record_value(record, "ip_profile"),
                        name=ip_group_name,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            profile_name = record_value(record, "ip_profile", "profile_name")
            if profile_name and record.get("enable_srtp") is not None:
                objects.append(
                    IPProfile.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        profile_name=profile_name,
                        enable_srtp=record_bool(record, "enable_srtp"),
                        name=profile_name,
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
        return objects
