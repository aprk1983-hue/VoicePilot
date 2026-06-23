"""AudioCodes ``show ha-status`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import HACluster
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show ha-status"
PARSER_ID = "audiocodes_show_ha_status"
PARSER_VERSION = "1.0.0"


class AudioCodesShowHaStatusParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("ha status", "active node", "standby node", "sync state")
    identity_fields = ("active_node", "name")
    required_fields = ("active_node", "name")

    def validate(self, structured_data: JsonDict) -> list[str]:
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in AudioCodes SBC evidence"]
        if not any(record.get("active_node") or record.get("name") for record in records):
            return ["ha status evidence missing cluster identity"]
        return []

    def extract_findings(self, structured_data: JsonDict, context: ParserContext) -> list[ParserFinding]:
        findings: list[ParserFinding] = []
        for record in self._records(structured_data):
            cluster_state = (record_value(record, "cluster_state", "state") or "").lower()
            if cluster_state in {"failover", "failed_over"}:
                findings.append(
                    ParserFinding(
                        signal="ha_failover",
                        confidence=93.0,
                        detail="HA failover detected",
                        source_field="cluster_state",
                    )
                )
            sync_state = (record_value(record, "sync_state") or "").lower()
            if sync_state in {"out_of_sync", "failed", "desynchronized"}:
                findings.append(
                    ParserFinding(
                        signal="standby_synchronization_failure",
                        confidence=91.0,
                        detail="Standby synchronization failure",
                        source_field="sync_state",
                    )
                )
        return findings

    def extract_voice_objects(
        self,
        structured_data: JsonDict,
        context: ParserContext,
        *,
        confidence: float,
    ) -> list[VoiceObject]:
        record = self._records(structured_data)[0]
        return [
            HACluster.create(
                vendor=context.vendor,
                platform=context.platform or PLATFORM,
                hostname=sbc_hostname(context),
                source_parser=PARSER_ID,
                source_command=self.command,
                source_evidence_id=context.evidence_id or "",
                cluster_state=record_value(record, "cluster_state", "state"),
                active_node=record_value(record, "active_node", "name"),
                standby_node=record_value(record, "standby_node"),
                sync_state=record_value(record, "sync_state"),
                name=record_value(record, "active_node", "name") or "ha-cluster",
                confidence=confidence,
                metadata=dict(record),
            )
        ]
