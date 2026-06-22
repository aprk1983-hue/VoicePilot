"""Shared helpers for Microsoft Teams parser plugins."""

from __future__ import annotations

from parser.parser_context import ParserContext
from shared.types import JsonDict

VENDOR = "microsoft"
PLATFORM = "Teams Phone"


def default_teams_metadata(
    parser: object,
    structured_data: JsonDict,
    context: ParserContext,
) -> JsonDict:
    """Return baseline collection metadata for Teams PowerShell parsers."""
    metadata: JsonDict = {
        "vendor": getattr(parser, "vendor", VENDOR),
        "command": getattr(parser, "command", ""),
        "case_id": context.case_id,
        "device_id": context.device_id,
        "hostname": context.hostname,
        "platform": context.platform or PLATFORM,
    }
    metadata.update(structured_data)
    return metadata


def teams_hostname(context: ParserContext) -> str:
    return context.hostname or context.metadata.get("tenant_id") or "teams-tenant"
