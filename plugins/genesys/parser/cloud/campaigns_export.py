"""Genesys Cloud ``campaigns-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import Campaign
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "campaigns-export"
PARSER_ID = "genesys_campaigns_export"
PARSER_VERSION = "1.0.0"


class GenesysCampaignsExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('campaign_id', 'dialing', 'outbound')
    identity_fields = ('campaign_id', 'id')
    required_fields = ('campaign_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"failed", "stopped", "error"}:
                findings.append(ParserFinding(signal="outbound_campaign_failure", confidence=91.0, detail="Outbound campaign failure", source_field="state"))

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
            campaign_id = record_identity(record, "campaign_id", "id")
            campaign_name = record_value(record, "campaign_name", "name")
            objects.append(Campaign.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                campaign_id=campaign_id, campaign_name=campaign_name,
                state=record_value(record, "state", "status"),
                queue_id=record_value(record, "queue_id"),
                name=campaign_name or campaign_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
