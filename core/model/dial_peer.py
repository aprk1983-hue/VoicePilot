"""Canonical dial-peer object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_DIAL_PEER, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class DialPeer(VoiceObject):
    """Outbound or inbound dial-peer definition."""

    tag: str | int | None = None
    peer_type: str | None = None
    incoming_called_number: str | None = None
    destination_pattern: str | None = None
    session_target: str | None = None
    voice_class_codec: str | None = None
    voice_class_server_group: str | None = None
    preference: int | None = None
    shutdown: bool | None = None
    status: str | None = None

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
        tag: str | int | None = None,
        peer_type: str | None = None,
        incoming_called_number: str | None = None,
        destination_pattern: str | None = None,
        session_target: str | None = None,
        voice_class_codec: str | None = None,
        voice_class_server_group: str | None = None,
        preference: int | None = None,
        shutdown: bool | None = None,
        status: str | None = None,
        name: str | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> DialPeer:
        display_name = name or (f"dial-peer {tag}" if tag is not None else "dial-peer")
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_DIAL_PEER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display_name,
                description=description or display_name,
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            tag=tag,
            peer_type=peer_type,
            incoming_called_number=incoming_called_number,
            destination_pattern=destination_pattern,
            session_target=session_target,
            voice_class_codec=voice_class_codec,
            voice_class_server_group=voice_class_server_group,
            preference=preference,
            shutdown=shutdown,
            status=status,
        )
