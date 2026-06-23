"""Genesys Cloud ``organization-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import GenesysOrganization, GenesysRegion, Division
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "organization-export"
PARSER_ID = "genesys_organization_export"
PARSER_VERSION = "1.0.0"


class GenesysOrganizationExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('organization', 'domain', 'region')
    identity_fields = ('organization_id', 'organization_name', 'id')
    required_fields = ('organization_id', 'organization_name')

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "inactive", "suspended"}:
                findings.append(ParserFinding(signal="organization_unavailable", confidence=94.0, detail="Organization unavailable", source_field="state"))

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
            org_id = record_identity(record, "organization_id", "id")
            org_name = record_identity(record, "organization_name", "name")
            if org_id or org_name:
                objects.append(GenesysOrganization.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    organization_id=org_id, organization_name=org_name,
                    state=record_value(record, "state", "status"), domain=record_value(record, "domain"),
                    name=org_name, confidence=confidence, metadata=dict(record),
                ))
            region_id = record_value(record, "region_id")
            region_name = record_value(record, "region_name", "region")
            if region_id or region_name:
                objects.append(GenesysRegion.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    region_id=region_id, region_name=region_name, home_organization=org_id,
                    name=region_name, confidence=confidence, metadata=dict(record),
                ))
            division_id = record_value(record, "division_id")
            division_name = record_value(record, "division_name", "division")
            if division_id or division_name:
                objects.append(Division.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    division_id=division_id, division_name=division_name,
                    state=record_value(record, "division_state", "state"),
                    name=division_name, confidence=confidence, metadata=dict(record),
                ))

        return objects
