"""Canonical SIP user agent object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_SIP_UA, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class SipUA(VoiceObject):
    """SIP user agent operational state."""

    enabled: bool | None = None
    registered: bool | None = None
    registrar: str | None = None
    transport: str | None = None
    expires: int | None = None
    tls: bool | None = None
    authentication: str | None = None

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
        enabled: bool | None = None,
        registered: bool | None = None,
        registrar: str | None = None,
        transport: str | None = None,
        expires: int | None = None,
        tls: bool | None = None,
        authentication: str | None = None,
        name: str = "sip-ua",
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SipUA:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_SIP_UA,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description=description or "SIP user agent status",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            enabled=enabled,
            registered=registered,
            registrar=registrar,
            transport=transport,
            expires=expires,
            tls=tls,
            authentication=authentication,
        )
