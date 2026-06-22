"""Microsoft Teams ``Get-CsOnlinePstnUsage`` evidence parser."""

from __future__ import annotations

from model.teams_objects import TeamsPstnUsage
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from plugins.microsoft.parser.teams._base import TeamsPowerShellParser
from plugins.microsoft.parser.teams._evidence import record_identity
from plugins.microsoft.parser.teams._helpers import PLATFORM, VENDOR, teams_hostname
from shared.types import JsonDict

COMMAND = "get-csonlinepstnusage"
PARSER_ID = "microsoft_get_csonlinepstnusage"
PARSER_VERSION = "1.0.0"


class MicrosoftGetCsOnlinePstnUsageParser(TeamsPowerShellParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("usage", "pstnusage", "onlinepstnusage")
    identity_fields = ("usage", "identity")
    required_fields = ("usage",)

    def validate(self, structured_data: JsonDict) -> list[str]:
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in Teams PowerShell evidence"]
        for index, record in enumerate(records):
            if record_identity(record, "usage", "identity") is None:
                errors.append(f"record {index} missing PSTN usage")
        return errors

    def extract_voice_objects(self, structured_data: JsonDict, context: ParserContext, *, confidence: float) -> list[VoiceObject]:
        objects: list[VoiceObject] = []
        for record in self._records(structured_data):
            usage = record_identity(record, "usage", "identity")
            objects.append(
                TeamsPstnUsage.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=teams_hostname(context),
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    usage=usage,
                    name=usage or "pstn-usage",
                    confidence=confidence,
                    metadata=dict(record),
                )
            )
        return objects
