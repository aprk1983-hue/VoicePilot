"""Bootstrap a default ParserEngine with registered vendor parsers."""

from __future__ import annotations

from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry


def build_default_parser_engine() -> ParserEngine | None:
    """Build a ParserEngine with Cisco parsers registered when available."""
    try:
        from plugins.cisco.parser import register_cisco_parsers
    except ImportError:
        return None

    registry = ParserRegistry()
    register_cisco_parsers(registry)
    return ParserEngine(registry=registry)
