"""Registry for VoicePilot brain engines."""

from __future__ import annotations

from typing import Dict, Type

from domain.interfaces import BrainEngine, LoggerPort
from runtime.exceptions import EngineAlreadyRegisteredError, EngineNotRegisteredError
from shared.types import EngineName


# Known engine names for registration skeleton (implementations are future sprints).
KNOWN_ENGINES: tuple[EngineName, ...] = (
    "InvestigationPlanner",
    "ReasoningEngine",
    "EvidenceEngine",
    "QuestionEngine",
    "ConfidenceEngine",
    "DecisionEngine",
    "TimelineEngine",
    "ReportEngine",
    "LearningEngine",
    "InvestigationEngine",
    "PlaybookEngine",
    "TopologyEngine",
    "CostOptimizer",
    "InvestigationGraph",
)


class EngineRegistry:
    """Registers brain engine types or instances by name.

    Does not implement engine behavior — registration and lookup only.
    """

    def __init__(self, logger: LoggerPort | None = None) -> None:
        self._engines: Dict[EngineName, Type[BrainEngine] | BrainEngine] = {}
        self._logger = logger

    def register(self, name: EngineName, engine: Type[BrainEngine] | BrainEngine) -> None:
        """Register an engine class or instance under ``name``."""
        if name in self._engines:
            raise EngineAlreadyRegisteredError(name)
        self._engines[name] = engine
        if self._logger:
            self._logger.info("Engine registered", engine_name=name)

    def unregister(self, name: EngineName) -> None:
        """Remove an engine registration."""
        if name not in self._engines:
            raise EngineNotRegisteredError(name)
        del self._engines[name]

    def get(self, name: EngineName) -> Type[BrainEngine] | BrainEngine:
        """Return registered engine by name."""
        if name not in self._engines:
            raise EngineNotRegisteredError(name)
        return self._engines[name]

    def is_registered(self, name: EngineName) -> bool:
        """Return whether ``name`` is registered."""
        return name in self._engines

    def list_registered(self) -> list[EngineName]:
        """Return sorted list of registered engine names."""
        return sorted(self._engines.keys())

    def register_defaults(self) -> None:
        """Register placeholder entries for known engine names.

        TODO: Replace placeholders with real engine classes when implemented.
        """
        for name in KNOWN_ENGINES:
            if not self.is_registered(name):
                self._engines[name] = _PlaceholderEngine
                if self._logger:
                    self._logger.debug("Placeholder engine registered", engine_name=name)


class _PlaceholderEngine:
    """Placeholder type until engine implementations exist."""

    name: str = "PlaceholderEngine"
