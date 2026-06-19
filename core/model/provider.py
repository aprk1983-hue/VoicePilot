"""Canonical SIP provider / trunk object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_PROVIDER, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class Provider(VoiceObject):
    """SIP trunk or ITSP provider endpoint."""

    transport: str | None = None
    addresses: tuple[str, ...] = ()
    status: str | None = None

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
        transport: str | None = None,
        addresses: tuple[str, ...] | None = None,
        status: str | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Provider:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_PROVIDER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description=description or f"Provider {name}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            transport=transport,
            addresses=addresses or (),
            status=status,
        )
