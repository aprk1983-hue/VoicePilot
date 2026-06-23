"""Genesys Cloud ``queue-members-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import QueueMember
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "queue-members-export"
PARSER_ID = "genesys_queue_members_export"
PARSER_VERSION = "1.0.0"


class GenesysQueueMembersExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('queue_id', 'member_id', 'user_id')
    identity_fields = ('member_id', 'id')
    required_fields = ('member_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "offline", "inactive"}:
                findings.append(ParserFinding(signal="queue_member_unavailable", confidence=91.0, detail="Queue member unavailable", source_field="state"))

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
            member_id = record_identity(record, "member_id", "id")
            objects.append(QueueMember.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                member_id=member_id, queue_id=record_value(record, "queue_id"),
                user_id=record_value(record, "user_id"), state=record_value(record, "state", "status"),
                name=member_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
