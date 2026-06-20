"""Deterministic knowledge pack matching for CVOM objects."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.knowledge_models import KnowledgeMatch, KnowledgePack
from knowledge.knowledge_registry import KnowledgeRegistry
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology


@dataclass(frozen=True)
class KnowledgeMatcher:
    """Match voice objects to applicable knowledge packs."""

    registry: KnowledgeRegistry

    def match_object(self, obj: VoiceObject) -> tuple[KnowledgePack, ...]:
        """Return knowledge packs whose scope and conditions match ``obj``."""
        matched: list[KnowledgePack] = []
        for pack in self.registry.search_by_object_type(obj.object_type):
            if not _scope_matches(pack, obj):
                continue
            if not _conditions_match(pack, obj):
                continue
            matched.append(pack)
        return tuple(matched)

    def match_topology(self, topology: VoiceTopology) -> tuple[KnowledgeMatch, ...]:
        """Return all object-to-pack matches across a topology."""
        matches: list[KnowledgeMatch] = []
        for obj in sorted(topology.all_objects(), key=lambda item: item.id):
            for pack in self.match_object(obj):
                matches.append(_build_match(pack, obj))
        return tuple(sorted(matches, key=_match_sort_key))


def _build_match(pack: KnowledgePack, obj: VoiceObject) -> KnowledgeMatch:
    return KnowledgeMatch(
        pack_id=pack.id,
        object_id=obj.id,
        object_type=obj.object_type,
        title=pack.title,
        category=pack.category,
        severity=pack.severity,
        recommendations=pack.recommendations,
        references=pack.references,
    )


def _scope_matches(pack: KnowledgePack, obj: VoiceObject) -> bool:
    if pack.vendor not in {"*", "any", ""} and pack.vendor.lower() != obj.vendor.lower():
        return False
    if pack.platform not in {"*", "any", ""} and pack.platform.lower() != obj.platform.lower():
        return False
    return True


def _conditions_match(pack: KnowledgePack, obj: VoiceObject) -> bool:
    if not pack.conditions:
        return True

    for key, expected in pack.conditions.items():
        actual = _resolve_condition_value(obj, key)
        if not _values_equal(actual, expected):
            return False
    return True


def _resolve_condition_value(obj: VoiceObject, key: str):
    if hasattr(obj, key):
        return getattr(obj, key)
    if key in obj.metadata:
        return obj.metadata[key]
    return None


def _values_equal(actual, expected) -> bool:
    if isinstance(expected, list):
        return any(_values_equal(actual, item) for item in expected)
    if isinstance(expected, str) and expected.strip().lower() == "missing":
        return _is_missing(actual)
    if isinstance(expected, str) and isinstance(actual, str):
        return actual.strip().lower() == expected.strip().lower()
    return actual == expected


def _is_missing(actual) -> bool:
    if actual is None:
        return True
    if isinstance(actual, str) and not actual.strip():
        return True
    return False


def _match_sort_key(match: KnowledgeMatch) -> tuple[str, str]:
    return (match.object_id, match.pack_id)
