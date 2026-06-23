"""Genesys Cloud ``byoc-cloud-trunks-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import ByocCloudTrunk, SipEndpoint
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "byoc-cloud-trunks-export"
PARSER_ID = "genesys_byoc_cloud_trunks_export"
PARSER_VERSION = "1.0.0"


class GenesysByocCloudTrunksExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('byoc', 'cloud', 'trunk')
    identity_fields = ('trunk_id', 'id')
    required_fields = ('trunk_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status") or "").lower()
            if state in {"unavailable", "down", "inactive"}:
                findings.append(ParserFinding(signal="byoc_cloud_trunk_failure", confidence=93.0, detail="BYOC Cloud trunk failure", source_field="state"))
            options = (record_value(record, "sip_options_status", "options_status") or "").lower()
            if options in {"failed", "failure", "503"}:
                findings.append(ParserFinding(signal="sip_options_failure", confidence=89.0, detail="SIP OPTIONS failed", source_field="sip_options_status"))
            carrier = (record_value(record, "carrier_status", "carrier_reachability") or "").lower()
            if carrier in {"unreachable", "down", "failed", "unavailable"}:
                findings.append(ParserFinding(signal="carrier_unreachable", confidence=90.0, detail="Carrier unreachable", source_field="carrier_status"))
            cert = (record_value(record, "certificate_status", "tls_certificate_status") or "").lower()
            if cert in {"expired", "invalid"}:
                findings.append(ParserFinding(signal="tls_certificate_expired", confidence=95.0, detail="TLS certificate expired", source_field="certificate_status"))
            tls = (record_value(record, "tls_status", "tls_negotiation_status") or "").lower()
            if tls in {"failed", "error", "negotiation_failed"}:
                findings.append(ParserFinding(signal="tls_negotiation_failure", confidence=92.0, detail="TLS negotiation failure", source_field="tls_status"))

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
            objects.append(ByocCloudTrunk.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                trunk_id=trunk_id, trunk_name=trunk_name,
                state=record_value(record, "state", "status"),
                sip_options_status=record_value(record, "sip_options_status", "options_status"),
                name=trunk_name or trunk_id, confidence=confidence, metadata=dict(record),
            ))
            endpoint = record_value(record, "sip_endpoint", "address")
            if endpoint:
                objects.append(SipEndpoint.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    endpoint_id=trunk_id, endpoint_name=trunk_name, address=endpoint,
                    transport=record_value(record, "transport"),
                    name=endpoint, confidence=confidence, metadata=dict(record),
                ))

        return objects
