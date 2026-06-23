"""Shared helpers for Genesys Cloud parsers."""

from __future__ import annotations

from parser.parser_context import ParserContext
from shared.types import JsonDict

VENDOR = "genesys"
PLATFORM = "Genesys Cloud"
PARSER_VERSION = "1.0.0"


def genesys_hostname(context: ParserContext) -> str:
    return context.hostname or "genesys-cloud.example.com"


def default_genesys_metadata(
    parser: object,
    structured_data: JsonDict,
    context: ParserContext,
) -> JsonDict:
    return {
        "vendor": getattr(parser, "vendor", VENDOR),
        "command": getattr(parser, "command", ""),
        "case_id": context.case_id,
        "device_id": context.device_id,
        "format": structured_data.get("format"),
        "record_count": structured_data.get("record_count"),
    }


def record_value(record: JsonDict, *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def record_bool(record: JsonDict, *keys: str) -> bool | None:
    value = record_value(record, *keys)
    if value is None:
        return None
    normalized = value.lower()
    if normalized in {"true", "yes", "enabled", "active", "on", "1", "published"}:
        return True
    if normalized in {"false", "no", "disabled", "inactive", "off", "0", "unpublished"}:
        return False
    return None


def record_int(record: JsonDict, *keys: str) -> int | None:
    value = record_value(record, *keys)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def record_identity(record: JsonDict, *fields: str) -> str | None:
    return record_value(record, *fields)
