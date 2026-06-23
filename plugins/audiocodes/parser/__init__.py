"""AudioCodes parser plugin registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.audiocodes.parser.sbc import register_audiocodes_sbc_parsers


def register_audiocodes_parsers(registry: ParserRegistry) -> None:
    """Register all AudioCodes parsers."""
    register_audiocodes_sbc_parsers(registry)
