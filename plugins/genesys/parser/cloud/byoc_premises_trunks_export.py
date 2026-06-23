"""Genesys Cloud ``byoc-premises-trunks-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import ByocPremisesTrunk
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "byoc-premises-trunks-export"
PARSER_ID = "genesys_byoc_premises_trunks_export"
PARSER_VERSION = "1.0.0"


class GenesysByocPremisesTrunksExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('byoc', 'premises', 'edge')
    identity_fields = ('trunk_id', 'id')
    required_fields = ('trunk_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "down"}:
                findings.append(ParserFinding(signal="byoc_premises_edge_unavailable", confidence=92.0, detail="BYOC Premises Edge unavailable", source_field="state"))

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
            trunk_id = record_identity(record, "trunk_id", "id")
            trunk_name = record_value(record, "trunk_name", "name")
            objects.append(ByocPremisesTrunk.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                trunk_id=trunk_id, trunk_name=trunk_name,
                state=record_value(record, "state", "status"),
                edge_id=record_value(record, "edge_id"),
                name=trunk_name or trunk_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
