"""Genesys Cloud ``data-actions-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import DataAction
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "data-actions-export"
PARSER_ID = "genesys_data_actions_export"
PARSER_VERSION = "1.0.0"


class GenesysDataActionsExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('data_action', 'endpoint', 'integration')
    identity_fields = ('action_id', 'id')
    required_fields = ('action_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"failed", "error", "unavailable"}:
                findings.append(ParserFinding(signal="data_action_failure", confidence=91.0, detail="Data Action failure", source_field="state"))

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
            action_id = record_identity(record, "action_id", "id")
            action_name = record_value(record, "action_name", "name")
            objects.append(DataAction.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                action_id=action_id, action_name=action_name,
                state=record_value(record, "state", "status"),
                endpoint_url=record_value(record, "endpoint_url", "url"),
                name=action_name or action_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
