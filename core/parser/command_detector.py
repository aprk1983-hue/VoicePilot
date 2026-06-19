"""Automatic CLI command detection from raw engineer-pasted output."""

from __future__ import annotations

from dataclasses import dataclass

from parser.parser_context import ParserContext

# Canonical command catalog — fingerprinting logic is implemented in future sprints.
KNOWN_COMMANDS: tuple[str, ...] = (
    "show version",
    "show sip-ua status",
    "show dial-peer voice summary",
    "show running-config",
    "debug ccsip messages",
    "show call active voice brief",
    "show voice class codec",
    "show license summary",
    "show inventory",
    "show platform",
)


@dataclass(frozen=True)
class DetectedCommand:
    """Result of command detection against raw CLI output."""

    command: str
    confidence: float
    vendor_hint: str | None = None
    detection_method: str | None = None


class CommandDetector:
    """Detect the originating CLI command from pasted device output.

    Inspired by Wireshark dissector selection and Nmap service fingerprinting,
    this component identifies which parser should handle a blob of raw text
    before structured parsing begins.
    """

    def __init__(self, known_commands: tuple[str, ...] | None = None) -> None:
        self._known_commands = known_commands or KNOWN_COMMANDS

    @property
    def known_commands(self) -> tuple[str, ...]:
        """Commands the detector can attempt to recognize."""
        return self._known_commands

    def detect(
        self,
        raw_text: str,
        context: ParserContext | None = None,
    ) -> DetectedCommand | None:
        """Identify the CLI command that produced ``raw_text``.

        v1 architecture only — concrete fingerprinting is deferred to vendor
        parser packs (e.g. ``plugins/cisco/parser``).
        """
        return None

    def normalize_command(self, command: str) -> str:
        """Normalize a command string for registry lookup."""
        return " ".join(command.strip().lower().split())
