"""Canonical translation profile object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_TRANSLATION_PROFILE, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class TranslationProfile(VoiceObject):
    """Translation profile binding called and calling rules."""

    profile_id: str | None = None
    called_rule: str | None = None
    calling_rule: str | None = None

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
        profile_id: str,
        called_rule: str | None = None,
        calling_rule: str | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TranslationProfile:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TRANSLATION_PROFILE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=profile_id,
                description=description or f"Translation profile {profile_id}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            profile_id=profile_id,
            called_rule=called_rule,
            calling_rule=calling_rule,
        )
