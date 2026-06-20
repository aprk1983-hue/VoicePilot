"""Knowledge pack construction helpers."""

from __future__ import annotations

from knowledge.knowledge_categories import KnowledgeCategory
from knowledge.knowledge_models import KnowledgePack
from knowledge.knowledge_schema import validate_pack_data
from knowledge.knowledge_severity import KnowledgeSeverity
from shared.types import JsonDict


def build_knowledge_pack(data: JsonDict) -> KnowledgePack:
    """Build a validated ``KnowledgePack`` from raw mapping data."""
    validated = validate_pack_data(data)
    return KnowledgePack(
        id=validated["id"],
        title=validated["title"],
        description=validated["description"],
        vendor=validated["vendor"],
        platform=validated["platform"],
        category=KnowledgeCategory(validated["category"]),
        severity=KnowledgeSeverity(validated["severity"]),
        supported_object_types=tuple(validated["supported_object_types"]),
        conditions=dict(validated["conditions"]),
        recommendations=tuple(validated["recommendations"]),
        references=tuple(validated.get("references", [])),
        metadata=dict(validated.get("metadata", {})),
        version=validated.get("version", "1.0"),
    )
