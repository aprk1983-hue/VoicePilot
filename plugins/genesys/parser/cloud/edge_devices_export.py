"""Genesys Cloud ``edge-devices-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import EdgeDevice
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "edge-devices-export"
PARSER_ID = "genesys_edge_devices_export"
PARSER_VERSION = "1.0.0"


class GenesysEdgeDevicesExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('edge_id', 'edge_name', 'telephony')
    identity_fields = ('edge_id', 'id')
    required_fields = ('edge_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"offline", "down", "inactive"}:
                findings.append(ParserFinding(signal="edge_offline", confidence=93.0, detail="Edge offline", source_field="state"))

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
            edge_id = record_identity(record, "edge_id", "id")
            edge_name = record_value(record, "edge_name", "name")
            objects.append(EdgeDevice.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                edge_id=edge_id, edge_name=edge_name,
                state=record_value(record, "state", "status"),
                organization_id=record_value(record, "organization_id"),
                software_version=record_value(record, "software_version", "version"),
                name=edge_name or edge_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
