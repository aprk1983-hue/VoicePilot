"""Structured logging adapter."""

from __future__ import annotations

import logging
from typing import Any

from domain.interfaces import LoggerPort


class StructuredLogger(LoggerPort):
    """Standard library logging adapter implementing ``LoggerPort``."""

    def __init__(self, name: str = "voicepilot", level: str = "INFO") -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def info(self, message: str, **context: object) -> None:
        self._logger.info(self._format(message, context))

    def error(self, message: str, **context: object) -> None:
        self._logger.error(self._format(message, context))

    def debug(self, message: str, **context: object) -> None:
        self._logger.debug(self._format(message, context))

    @staticmethod
    def _format(message: str, context: dict[str, Any]) -> str:
        if not context:
            return message
        pairs = " ".join(f"{k}={v!r}" for k, v in context.items())
        return f"{message} | {pairs}"
