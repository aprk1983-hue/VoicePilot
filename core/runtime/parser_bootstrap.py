"""Bootstrap a default ParserEngine with registered vendor parsers."""

from __future__ import annotations

from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry


def build_default_parser_engine() -> ParserEngine | None:
    """Build a ParserEngine with registered vendor parsers when available."""
    registry = ParserRegistry()
    registered = False

    try:
        from plugins.cisco.parser import register_cisco_parsers

        register_cisco_parsers(registry)
        registered = True
    except ImportError:
        pass

    try:
        from plugins.microsoft.parser import register_microsoft_parsers

        register_microsoft_parsers(registry)
        registered = True
    except ImportError:
        pass

    try:
        from plugins.audiocodes.parser import register_audiocodes_parsers

        register_audiocodes_parsers(registry)
        registered = True
    except ImportError:
        pass

    if not registered:
        return None
    return ParserEngine(registry=registry)
