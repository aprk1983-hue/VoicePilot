"""Deterministic snapshot content hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from model.voice_graph import VoiceObject, VoiceRelationship


def compute_snapshot_hash(
    voice_objects: tuple[VoiceObject, ...],
    relationships: tuple[VoiceRelationship, ...],
) -> str:
    """Return a deterministic SHA256 hash for canonical snapshot content."""
    payload = {
        "relationships": _canonical_relationships(relationships),
        "voice_objects": _canonical_voice_objects(voice_objects),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_voice_objects(
    voice_objects: tuple[VoiceObject, ...],
) -> list[dict[str, Any]]:
    return [
        _normalize_mapping(asdict(obj))
        for obj in sorted(voice_objects, key=lambda item: item.id)
    ]


def _canonical_relationships(
    relationships: tuple[VoiceRelationship, ...],
) -> list[dict[str, Any]]:
    return [
        _normalize_mapping(asdict(relationship))
        for relationship in sorted(relationships, key=lambda item: item.relationship_id)
    ]


def _normalize_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_mapping(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize_mapping(item) for item in value]
    return value
