"""Top-level parser orchestrator."""

from __future__ import annotations

from parser.command_detector import CommandDetector
from parser.parser_context import ParserContext
from parser.parser_exceptions import CommandDetectionError, ParserNotFoundError
from parser.parser_registry import ParserRegistry
from parser.parser_result import ParserResult


class ParserEngine:
    """Coordinate command detection, parser lookup, and structured parsing.

    The parser engine is runtime-adjacent but domain-pure: it never reads or
    mutates ``Case`` objects. Callers pass ``ParserContext`` and raw text;
    callers decide how to persist ``ParserResult`` artifacts.
    """

    def __init__(
        self,
        registry: ParserRegistry | None = None,
        detector: CommandDetector | None = None,
    ) -> None:
        self._registry = registry or ParserRegistry()
        self._detector = detector or CommandDetector()

    @property
    def registry(self) -> ParserRegistry:
        """Registered vendor command parsers."""
        return self._registry

    @property
    def detector(self) -> CommandDetector:
        """CLI command detector."""
        return self._detector

    def parse(
        self,
        raw_text: str,
        context: ParserContext,
        *,
        command: str | None = None,
    ) -> ParserResult:
        """Parse raw CLI output into a structured result.

        When ``command`` is omitted, the engine delegates to
        ``CommandDetector``. When provided, detection is skipped and the
        registry resolves the parser directly.
        """
        resolved_command = command
        if resolved_command is None:
            detected = self._detector.detect(raw_text, context)
            if detected is None:
                raise CommandDetectionError()
            resolved_command = detected.command

        normalized_command = self._detector.normalize_command(resolved_command)
        try:
            parser = self._registry.get_parser(context.vendor, normalized_command)
        except ParserNotFoundError as exc:
            raise ParserNotFoundError(context.vendor, normalized_command) from exc

        return parser.parse(raw_text, context)
