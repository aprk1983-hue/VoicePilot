"""Canonical translation rule object."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import OBJECT_TYPE_TRANSLATION_RULE, VoiceObject, base_object_fields
from shared.types import JsonDict


@dataclass(frozen=True)
class TranslationRule(VoiceObject):
    """Number translation rule set."""

    rule_id: str | None = None
    rules: tuple[str, ...] = ()

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
        rule_id: str,
        rules: tuple[str, ...] | None = None,
        description: str = "",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TranslationRule:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TRANSLATION_RULE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=rule_id,
                description=description or f"Translation rule {rule_id}",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            rule_id=rule_id,
            rules=rules or (),
        )
