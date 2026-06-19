"""Parser framework ports and abstract base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict


class CommandParser(ABC):
    """Vendor command parser contract.

    Every vendor-specific parser (Cisco, Microsoft Teams, Ribbon, AudioCodes)
    implements this interface. Parsers are pure functions over raw text and
    context — they never read or mutate ``Case`` aggregates.
    """

    vendor: str
    command: str
    parser_version: str

    @abstractmethod
    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        """Return whether this parser recognizes the given CLI output."""

    @abstractmethod
    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        """Parse raw CLI output into a structured ``ParserResult``."""

    @abstractmethod
    def validate(self, structured_data: JsonDict) -> list[str]:
        """Validate structured parse output.

        Returns an empty list when valid; otherwise human-readable error messages.
        """

    @abstractmethod
    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        """Derive investigation findings from structured parse output."""

    @abstractmethod
    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        """Derive device and collection metadata from structured parse output."""
