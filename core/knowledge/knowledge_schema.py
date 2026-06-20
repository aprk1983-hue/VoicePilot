"""Schema validation for VKF knowledge packs."""

from __future__ import annotations

from knowledge.knowledge_categories import KnowledgeCategory
from knowledge.knowledge_exceptions import KnowledgeSchemaError
from knowledge.knowledge_severity import KnowledgeSeverity
from shared.types import JsonDict

_REQUIRED_FIELDS = (
    "id",
    "title",
    "description",
    "vendor",
    "platform",
    "category",
    "severity",
    "supported_object_types",
    "conditions",
    "recommendations",
    "version",
)


def validate_pack_data(data: JsonDict) -> JsonDict:
    """Validate and normalize raw knowledge pack data."""
    if not isinstance(data, dict):
        raise KnowledgeSchemaError("Knowledge pack root must be a mapping")

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise KnowledgeSchemaError(f"Missing required fields: {', '.join(missing)}")

    pack_id = _require_non_empty_string(data["id"], field="id")
    title = _require_non_empty_string(data["title"], field="title")
    description = _require_non_empty_string(data["description"], field="description")
    vendor = _require_non_empty_string(data["vendor"], field="vendor")
    platform = _require_non_empty_string(data["platform"], field="platform")
    version = _require_non_empty_string(data["version"], field="version")

    category = _require_enum_value(data["category"], KnowledgeCategory, field="category")
    severity = _require_enum_value(data["severity"], KnowledgeSeverity, field="severity")
    supported_object_types = _require_string_list(
        data["supported_object_types"],
        field="supported_object_types",
        allow_empty=False,
    )
    conditions = _require_mapping(data["conditions"], field="conditions")
    recommendations = _require_string_list(
        data["recommendations"],
        field="recommendations",
        allow_empty=False,
    )
    references = _require_string_list(
        data.get("references", []),
        field="references",
        allow_empty=True,
    )
    metadata = _require_mapping(data.get("metadata", {}), field="metadata")

    return {
        "id": pack_id,
        "title": title,
        "description": description,
        "vendor": vendor,
        "platform": platform,
        "category": category,
        "severity": severity,
        "supported_object_types": supported_object_types,
        "conditions": conditions,
        "recommendations": recommendations,
        "references": references,
        "metadata": metadata,
        "version": version,
    }


def _require_non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeSchemaError(f"Field '{field}' must be a non-empty string")
    return value.strip()


def _require_string_list(value: object, *, field: str, allow_empty: bool) -> list[str]:
    if not isinstance(value, list):
        raise KnowledgeSchemaError(f"Field '{field}' must be a list")
    if not allow_empty and not value:
        raise KnowledgeSchemaError(f"Field '{field}' must not be empty")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise KnowledgeSchemaError(f"Field '{field}[{index}]' must be a non-empty string")
        normalized.append(item.strip())
    return normalized


def _require_mapping(value: object, *, field: str) -> dict:
    if not isinstance(value, dict):
        raise KnowledgeSchemaError(f"Field '{field}' must be a mapping")
    return value


def _require_enum_value(value: object, enum_type, *, field: str) -> str:
    if not isinstance(value, str):
        raise KnowledgeSchemaError(f"Field '{field}' must be a string")
    normalized = value.strip().lower()
    valid = {member.value for member in enum_type}
    if normalized not in valid:
        raise KnowledgeSchemaError(
            f"Field '{field}' must be one of: {', '.join(sorted(valid))}"
        )
    return normalized
