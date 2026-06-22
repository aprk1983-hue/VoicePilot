"""Microsoft parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.microsoft.parser.teams import register_teams_parsers


def register_microsoft_parsers(registry: ParserRegistry) -> None:
    """Register all Microsoft command parsers with the given registry."""
    register_teams_parsers(registry)
