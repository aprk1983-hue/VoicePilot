"""Canonical server group object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_SERVER_GROUP, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class ServerGroup(VoiceObject):
    """SIP server group for trunk or registrar selection."""

    server_group_id: str | None = None
    servers: tuple[str, ...] = ()
    preference: int | None = None

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
        server_group_id: str,
        servers: tuple[str, ...] | None = None,
        preference: int | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ServerGroup:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_SERVER_GROUP,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=server_group_id,
                description=description or f"Server group {server_group_id}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            server_group_id=server_group_id,
            servers=servers or (),
            preference=preference,
        )
