"""Canonical voice service configuration object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_VOICE_SERVICE, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class VoiceService(VoiceObject):
    """Platform voice service policy (e.g. voice service voip)."""

    allow_connections: bool | None = None
    bind_control: str | None = None
    bind_media: str | None = None
    trusted_ips: tuple[str, ...] = ()
    early_offer: bool | None = None
    options_ping: bool | None = None
    supplementary_services: tuple[str, ...] = ()

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
        allow_connections: bool | None = None,
        bind_control: str | None = None,
        bind_media: str | None = None,
        trusted_ips: tuple[str, ...] | None = None,
        early_offer: bool | None = None,
        options_ping: bool | None = None,
        supplementary_services: tuple[str, ...] | None = None,
        name: str = "voice-service",
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> VoiceService:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_VOICE_SERVICE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description=description or "Voice service configuration",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            allow_connections=allow_connections,
            bind_control=bind_control,
            bind_media=bind_media,
            trusted_ips=trusted_ips or (),
            early_offer=early_offer,
            options_ping=options_ping,
            supplementary_services=supplementary_services or (),
        )
