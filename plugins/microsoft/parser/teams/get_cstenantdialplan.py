"""Microsoft Teams ``Get-CsTenantDialPlan`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsDialPlan
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import parse_int, record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-cstenantdialplan"
PARSER_ID = "microsoft_get_cstenantdialplan"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsTenantDialPlanParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("normalizationrules", "dialplan", "externalaccessprefix", "tenantdialplan")
    identity_fields = ("identity",)
    required_fields = ("identity",)

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            count = parse_int(record.get("normalization_rules_count"))
            if count == 0:
                findings.append(ParserFinding(signal="normalization_rule_failure", confidence=85.0, detail="Dial plan has no normalization rules", source_field="normalization_rules_count"))
        return findings

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            identity = record_identity(record, "identity")
            rules = record.get("normalization_rules")
            count = parse_int(record.get("normalization_rules_count"))
            if count is None and isinstance(rules, list):
                count = len(rules)
            objects.append(
                TeamsDialPlan.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    normalization_rules_count=count,
                    external_access_prefix=record.get("external_access_prefix"),
                    name=identity or "dial-plan",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
