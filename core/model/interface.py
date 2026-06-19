"""Canonical network interface object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_INTERFACE, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class Interface(VoiceObject):
    """Network interface attached to a voice device."""

    ip: str | None = None
    mask: str | None = None
    status: str | None = None
    vrf: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        name: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        ip: str | None = None,
        mask: str | None = None,
        status: str | None = None,
        vrf: str | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Interface:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_INTERFACE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description=description or f"Interface {name}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            ip=ip,
            mask=mask,
            status=status,
            vrf=vrf,
        )
