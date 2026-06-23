"""Genesys Cloud ``agents-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import Agent
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "agents-export"
PARSER_ID = "genesys_agents_export"
PARSER_VERSION = "1.0.0"


class GenesysAgentsExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('agent_id', 'routing_status', 'interacting')
    identity_fields = ('agent_id', 'id')
    required_fields = ('agent_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"offline", "logged_out", "logged out"}:
                findings.append(ParserFinding(signal="agent_not_logged_in", confidence=90.0, detail="Agent not logged in", source_field="state"))
            if state in {"interacting", "stuck_interacting"}:
                findings.append(ParserFinding(signal="agent_stuck_interacting", confidence=91.0, detail="Agent stuck interacting", source_field="state"))

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
            agent_id = record_identity(record, "agent_id", "id")
            objects.append(Agent.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                agent_id=agent_id, user_id=record_value(record, "user_id"),
                display_name=record_value(record, "display_name", "name"),
                state=record_value(record, "state", "status"),
                queue_id=record_value(record, "queue_id"),
                name=record_value(record, "display_name", "name") or agent_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
