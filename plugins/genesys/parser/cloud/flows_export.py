"""Genesys Cloud ``flows-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import Flow, WrapUpCode
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "flows-export"
PARSER_ID = "genesys_flows_export"
PARSER_VERSION = "1.0.0"


class GenesysFlowsExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('flow_id', 'flow_name', 'inbound')
    identity_fields = ('flow_id', 'id')
    required_fields = ('flow_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"failed", "error", "invalid"}:
                findings.append(ParserFinding(signal="call_flow_failure", confidence=91.0, detail="Call flow failure", source_field="state"))

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
            objects.append(Flow.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                flow_id=flow_id, flow_name=flow_name,
                state=record_value(record, "state", "status"),
                target_queue=record_value(record, "target_queue", "queue_id"),
                name=flow_name or flow_id, confidence=confidence, metadata=dict(record),
            ))
            code_id = record_value(record, "wrap_up_code_id", "code_id")
            code_name = record_value(record, "wrap_up_code_name", "wrap_up_code")
            if code_id or code_name:
                objects.append(WrapUpCode.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    code_id=code_id, code_name=code_name, flow_id=flow_id,
                    name=code_name or code_id, confidence=confidence, metadata=dict(record),
                ))

        return objects
