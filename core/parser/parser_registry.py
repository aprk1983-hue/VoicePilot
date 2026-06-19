"""Registry for vendor command parsers."""

from __future__ import annotations

from parser.interfaces import CommandParser
from parser.parser_exceptions import ParserAlreadyRegisteredError, ParserNotFoundError


class ParserRegistry:
    """Register and resolve parsers by vendor and command.

    Supports multiple vendors side by side. Cisco parsers live under
    ``plugins/cisco/parser``; future vendors follow the same layout.
    """

    def __init__(self) -> None:
        self._parsers: dict[tuple[str, str], CommandParser] = {}

    def register(self, parser: CommandParser) -> None:
        """Register a parser instance for its vendor/command pair."""
        key = self._key(parser.vendor, parser.command)
        if key in self._parsers:
            raise ParserAlreadyRegisteredError(parser.vendor, parser.command)
        self._parsers[key] = parser

    def unregister(self, vendor: str, command: str) -> None:
        """Remove a parser from the registry."""
        self._parsers.pop(self._key(vendor, command), None)

    def get_parser(self, vendor: str, command: str) -> CommandParser:
        """Resolve a parser by vendor and normalized command."""
        parser = self._parsers.get(self._key(vendor, command))
        if parser is None:
            raise ParserNotFoundError(vendor, command)
        return parser

    def has_parser(self, vendor: str, command: str) -> bool:
        """Return whether a parser is registered for the vendor/command pair."""
        return self._key(vendor, command) in self._parsers

    def list_vendors(self) -> tuple[str, ...]:
        """Return registered vendor identifiers."""
        return tuple(sorted({vendor for vendor, _ in self._parsers}))

    def list_commands(self, vendor: str | None = None) -> tuple[str, ...]:
        """Return registered commands, optionally filtered by vendor."""
        commands = [
            command
            for registered_vendor, command in self._parsers
            if vendor is None or registered_vendor == vendor
        ]
        return tuple(sorted(commands))

    def clear(self) -> None:
        """Remove all registered parsers."""
        self._parsers.clear()

    @staticmethod
    def _key(vendor: str, command: str) -> tuple[str, str]:
        normalized_vendor = vendor.strip().lower()
        normalized_command = " ".join(command.strip().lower().split())
        return normalized_vendor, normalized_command
