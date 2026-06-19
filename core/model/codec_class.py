"""Canonical codec class object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_CODEC_CLASS, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class CodecClass(VoiceObject):
    """Voice class codec preference list."""

    codec_class_id: str | None = None
    codecs: tuple[str, ...] = ()

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
        codec_class_id: str,
        codecs: tuple[str, ...] | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> CodecClass:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_CODEC_CLASS,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=codec_class_id,
                description=description or f"Codec class {codec_class_id}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            codec_class_id=codec_class_id,
            codecs=codecs or (),
        )
