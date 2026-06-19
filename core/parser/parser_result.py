"""Structured output produced by vendor command parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shared.types import JsonDict

if TYPE_CHECKING:
    from model.voice_graph import VoiceObject


@dataclass(frozen=True)
class ParserFinding:
    """A single investigative signal extracted from parsed CLI output."""

    signal: str
    confidence: float
    detail: str | None = None
    severity: str | None = None
    source_field: str | None = None


@dataclass
class ParserResult:
    """Complete result of parsing one CLI artifact.

    Parsers populate this object only. The runtime decides how findings map
    to ``AnalysisFinding``, hypotheses, and case timeline events.
    """

    command: str
    hostname: str | None = None
    platform: str | None = None
    ios_version: str | None = None
    parser_version: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
    structured_data: JsonDict = field(default_factory=dict)
    findings: list[ParserFinding] = field(default_factory=list)
    voice_objects: list[VoiceObject] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Return whether parsing completed without blocking errors."""
        return not self.errors
