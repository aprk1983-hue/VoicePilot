"""Genesys Cloud ``skills-export`` evidence parser."""

from __future__ import annotations

from model.genesys_objects import Skill
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.genesys.parser.cloud._base import GenesysCloudParser
from plugins.genesys.parser.cloud._helpers import PLATFORM, VENDOR, genesys_hostname, record_identity, record_value
from shared.types import JsonDict

COMMAND = "skills-export"
PARSER_ID = "genesys_skills_export"
PARSER_VERSION = "1.0.0"


class GenesysSkillsExportParser(GenesysCloudParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ('skill_id', 'skill_name', 'routing')
    identity_fields = ('skill_id', 'id')
    required_fields = ('skill_id',)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            pass
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
            skill_id = record_identity(record, "skill_id", "id")
            skill_name = record_value(record, "skill_name", "name")
            objects.append(Skill.create(
                vendor=context.vendor, platform=context.platform or PLATFORM, hostname=genesys_hostname(context),
                source_parser=PARSER_ID, source_command=self.command, source_evidence_id=context.evidence_id or "",
                skill_id=skill_id, skill_name=skill_name,
                state=record_value(record, "state", "status"),
                division_id=record_value(record, "division_id"),
                name=skill_name or skill_id, confidence=confidence, metadata=dict(record),
            ))

        return objects
