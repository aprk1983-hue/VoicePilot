"""Shared helpers for Cisco CUCM parser plugins."""

from __future__ import annotations

from parser.parser_context import ParserContext
from shared.types import JsonDict


def default_cucm_metadata(
    parser: object,
    structured_data: JsonDict,
    context: ParserContext,
) -> JsonDict:
    """Return baseline collection metadata for CUCM CLI parsers."""
    metadata: JsonDict = {
        "vendor": getattr(parser, "vendor", "cisco"),
        "command": getattr(parser, "command", ""),
        "case_id": context.case_id,
        "device_id": context.device_id,
        "hostname": context.hostname,
    }
    metadata.update(structured_data)
    return metadata
