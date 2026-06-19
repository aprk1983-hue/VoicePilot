"""VoicePilot parser framework — vendor-neutral CLI output parsing architecture."""

from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_exceptions import VoicePilotParserError
from parser.parser_registry import ParserRegistry
from parser.parser_result import ParserFinding, ParserResult

__all__ = [
    "CommandParser",
    "ParserContext",
    "ParserEngine",
    "ParserFinding",
    "ParserRegistry",
    "ParserResult",
    "VoicePilotParserError",
]
