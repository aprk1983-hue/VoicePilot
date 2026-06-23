"""Genesys Cloud ``queues-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import Queue
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "queues-export"
PARSER_ID = "genesys_queues_export"
PARSER_VERSION = "1.0.0"


class GenesysQueuesExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('queue_id', 'queue_name', 'acd')
    identity_fields = ('queue_id', 'id')
    required_fields = ('queue_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "disabled", "inactive"}:
                findings.append(ParserFinding(signal="queue_unavailable", confidence=92.0, detail="Queue unavailable", source_field="state"))
            waiting = record_value(record, "waiting_calls", "queue_depth", "offered_calls")
            if waiting and waiting.isdigit() and int(waiting) >= 50:
                findings.append(ParserFinding(signal="queue_overloaded", confidence=88.0, detail="Queue overloaded", source_field="waiting_calls"))

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
            queue_id = record_identity(record, "queue_id", "id")
            queue_name = record_value(record, "queue_name", "name")
            objects.append(Queue.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                queue_id=queue_id, queue_name=queue_name,
                state=record_value(record, "state", "status"),
                division_id=record_value(record, "division_id"),
                name=queue_name or queue_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
