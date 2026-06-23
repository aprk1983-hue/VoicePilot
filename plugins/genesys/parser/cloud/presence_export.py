"""Genesys Cloud ``presence-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import PresenceDefinition, UserRoutingStatus
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "presence-export"
PARSER_ID = "genesys_presence_export"
PARSER_VERSION = "1.0.0"


class GenesysPresenceExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('presence', 'routing_status', 'system_presence')
    identity_fields = ('presence_id', 'id')
    required_fields = ('presence_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            sync = (record_value(record, "sync_state", "synchronization") or "").lower()
            if sync in {"out_of_sync", "failed", "desynchronized"}:
                findings.append(ParserFinding(signal="presence_synchronization_failure", confidence=89.0, detail="Presence synchronization failure", source_field="sync_state"))

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
            presence_id = record_identity(record, "presence_id", "id")
            presence_name = record_value(record, "presence_name", "name")
            if presence_id or presence_name:
                objects.append(PresenceDefinition.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    presence_id=presence_id, presence_name=presence_name,
                    system_presence=record_value(record, "system_presence"),
                    name=presence_name or presence_id, confidence=confidence, metadata=dict(record),
                ))
            user_id = record_value(record, "user_id")
            if user_id:
                objects.append(UserRoutingStatus.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    user_id=user_id, routing_status=record_value(record, "routing_status"),
                    presence_id=presence_id,
                    name=user_id, confidence=confidence, metadata=dict(record),
                ))

        return objects
