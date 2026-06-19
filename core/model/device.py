"""Canonical voice device object."""

from __future__ import annotations

from dataclasses import dataclass, field

from model.interface import Interface
from model.voice_graph import OBJECT_TYPE_DEVICE, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class Device(VoiceObject):
    """Voice platform device (CUBE, SBC, gateway, etc.)."""

    ios_version: str | None = None
    serial: str | None = None
    model: str | None = None
    management_ip: str | None = None
    interfaces: tuple[Interface, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        ios_version: str | None = None,
        serial: str | None = None,
        model: str | None = None,
        management_ip: str | None = None,
        interfaces: tuple[Interface, ...] | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Device:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_DEVICE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=hostname,
                description=description or f"Device {hostname}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            ios_version=ios_version,
            serial=serial,
            model=model,
            management_ip=management_ip,
            interfaces=interfaces or (),
        )
