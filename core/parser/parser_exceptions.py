"""Parser framework exceptions."""

from __future__ import annotations


class VoicePilotParserError(Exception):
    """Base exception for parser framework errors."""


class ParserNotFoundError(VoicePilotParserError):
    """Raised when no parser is registered for a vendor/command pair."""

    def __init__(self, vendor: str, command: str) -> None:
        super().__init__(f"No parser registered for vendor={vendor!r}, command={command!r}")
        self.vendor = vendor
        self.command = command


class ParserAlreadyRegisteredError(VoicePilotParserError):
    """Raised when registering a duplicate vendor/command parser."""

    def __init__(self, vendor: str, command: str) -> None:
        super().__init__(f"Parser already registered for vendor={vendor!r}, command={command!r}")
        self.vendor = vendor
        self.command = command


class CommandDetectionError(VoicePilotParserError):
    """Raised when CLI output cannot be matched to a known command."""

    def __init__(self, message: str = "Unable to detect CLI command from raw output") -> None:
        super().__init__(message)


class ParserValidationError(VoicePilotParserError):
    """Raised when structured parser output fails validation."""

    def __init__(self, command: str, errors: list[str]) -> None:
        super().__init__(f"Parser validation failed for {command!r}: {'; '.join(errors)}")
        self.command = command
        self.errors = errors


class ParserExecutionError(VoicePilotParserError):
    """Raised when a parser fails during execution."""

    def __init__(self, command: str, message: str) -> None:
        super().__init__(f"Parser execution failed for {command!r}: {message}")
        self.command = command
