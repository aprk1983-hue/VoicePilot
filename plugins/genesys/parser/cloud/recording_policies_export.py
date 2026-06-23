"""Genesys Cloud ``recording-policies-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import RecordingPolicy, Recording
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "recording-policies-export"
PARSER_ID = "genesys_recording_policies_export"
PARSER_VERSION = "1.0.0"


class GenesysRecordingPoliciesExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('recording', 'policy', 'compliance')
    identity_fields = ('policy_id', 'id')
    required_fields = ('policy_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):

            state = (record_value(record, "state", "status", "recording_state") or "").lower()
            if state in {"failed", "missing", "error"}:
                findings.append(ParserFinding(signal="recording_failure", confidence=90.0, detail="Recording failure", source_field="state"))

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
            policy_id = record_identity(record, "policy_id", "id")
            policy_name = record_value(record, "policy_name", "name")
            objects.append(RecordingPolicy.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                policy_id=policy_id, policy_name=policy_name,
                state=record_value(record, "state", "status"),
                name=policy_name or policy_id, confidence=confidence, metadata=dict(record),
            ))
            recording_id = record_value(record, "recording_id")
            if recording_id:
                objects.append(Recording.create(
                    vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                    source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                    recording_id=recording_id, policy_id=policy_id,
                    state=record_value(record, "recording_state"),
                    name=recording_id, confidence=confidence, metadata=dict(record),
                ))

        return objects
