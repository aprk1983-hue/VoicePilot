"""AudioCodes ``show configuration`` evidence parser."""

from __future__ import annotations

from model.audiocodes_objects import (
    EthernetInterface,
    ManipulationSet,
    MediaSecurityProfile,
    MessageManipulation,
    SBCDevice,
    SRD,
)
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from plugins.audiocodes.parser.sbc._base import AudioCodesSbcParser
from plugins.audiocodes.parser.sbc._helpers import PLATFORM, VENDOR, record_value, sbc_hostname
from shared.types import JsonDict

COMMAND = "show configuration"
PARSER_ID = "audiocodes_show_configuration"
PARSER_VERSION = "1.0.0"


class AudioCodesShowConfigurationParser(AudioCodesSbcParser):
    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION
    detect_markers = ("device name", "software version", "manipulation set", "srd name")
    identity_fields = ("name", "device_name")
    required_fields = ("name", "device_name")

    def validate(self, structured_data: JsonDict) -> list[str]:
        records = structured_data.get("records") or []
        if not records:
            return ["no records found in AudioCodes SBC evidence"]
        if not any(record.get("device_name") or record.get("name") for record in records):
            return ["configuration evidence missing device identity"]
        return []

    def extract_voice_objects(
        self,
        structured_data: JsonDict,
        context: ParserContext,
        *,
        confidence: float,
    ) -> list[VoiceObject]:
        hostname = sbc_hostname(context)
        objects: list[VoiceObject] = []
        device_name = None
        for record in self._records(structured_data):
            if record.get("device_name"):
                device_name = record.get("device_name")
                break
        if device_name:
            device_record = next(
                (record for record in self._records(structured_data) if record.get("device_name")),
                {},
            )
            objects.append(
                SBCDevice.create(
                    vendor=context.vendor,
                    platform=context.platform or PLATFORM,
                    hostname=hostname,
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    device_name=str(device_name),
                    software_version=record_value(device_record, "software_version"),
                    device_status=record_value(device_record, "device_status"),
                    confidence=confidence,
                    metadata=dict(device_record),
                )
            )
        for record in self._records(structured_data):
            if record.get("srd_name"):
                objects.append(
                    SRD.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        srd_name=record.get("srd_name"),
                        state=record.get("state"),
                        name=str(record.get("srd_name")),
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            if record.get("manipulation_set_name") or record.get("set_name"):
                set_name = record.get("manipulation_set_name") or record.get("set_name")
                objects.append(
                    ManipulationSet.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        set_name=str(set_name),
                        state=record.get("state"),
                        name=str(set_name),
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            if record.get("manipulation_name"):
                objects.append(
                    MessageManipulation.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        manipulation_name=record.get("manipulation_name"),
                        set_name=record.get("set_name"),
                        action=record.get("action"),
                        name=str(record.get("manipulation_name")),
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            if record.get("ethernet_interface") or record.get("interface_name"):
                iface = record.get("ethernet_interface") or record.get("interface_name")
                objects.append(
                    EthernetInterface.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        interface_name=str(iface),
                        state=record.get("state"),
                        ip_address=record.get("ip_address"),
                        name=str(iface),
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
            if record.get("media_security_profile") or record.get("profile_name"):
                profile = record.get("media_security_profile") or record.get("profile_name")
                objects.append(
                    MediaSecurityProfile.create(
                        vendor=context.vendor,
                        platform=context.platform or PLATFORM,
                        hostname=hostname,
                        source_parser=PARSER_ID,
                        source_command=self.command,
                        source_evidence_id=context.evidence_id or "",
                        profile_name=str(profile),
                        srtp_mode=record.get("srtp_mode"),
                        name=str(profile),
                        confidence=confidence,
                        metadata=dict(record),
                    )
                )
        return objects
