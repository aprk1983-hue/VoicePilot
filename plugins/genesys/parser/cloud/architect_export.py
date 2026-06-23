"""Genesys Cloud ``architect-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import ArchitectFlow
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "architect-export"
PARSER_ID = "genesys_architect_export"
PARSER_VERSION = "1.0.0"


class GenesysArchitectExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('architect', 'publish', 'flow')
    identity_fields = ('flow_id', 'id')
    required_fields = ('flow_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            publish = (record_value(record, "publish_state", "status") or "").lower()
            if publish in {"failed", "unpublished", "error"}:
                findings.append(ParserFinding(signal="architect_publish_failure", confidence=92.0, detail="Architect publish issue", source_field="publish_state"))

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
            flow_id = record_identity(record, "flow_id", "id")
            flow_name = record_value(record, "flow_name", "name")
            objects.append(ArchitectFlow.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                flow_id=flow_id, flow_name=flow_name,
                publish_state=record_value(record, "publish_state", "status"),
                data_action_id=record_value(record, "data_action_id"),
                name=flow_name or flow_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
