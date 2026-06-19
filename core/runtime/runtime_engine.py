"""VoicePilot Runtime Engine — kernel orchestrator skeleton."""

from __future__ import annotations

from domain.interfaces import CaseRepository, LoggerPort, PlaybookRepository
from runtime.case_manager import CaseManager
from runtime.engine_registry import EngineRegistry
from runtime.event_bus import EventBus
from runtime.playbook_loader import PlaybookLoader
from runtime.state_machine import InvestigationStateMachine
from shared.config import RuntimeConfig


class RuntimeEngine:
    """Top-level runtime kernel orchestrator.

    Wires core runtime components. Investigation execution is a future sprint.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        case_repository: CaseRepository,
        playbook_repository: PlaybookRepository,
        logger: LoggerPort | None = None,
    ) -> None:
        self._config = config
        self._event_bus = EventBus(logger=logger)
        self._state_machine = InvestigationStateMachine()
        self._engine_registry = EngineRegistry(logger=logger)
        self._case_manager = CaseManager(
            repository=case_repository,
            state_machine=self._state_machine,
            event_bus=self._event_bus,
            logger=logger,
        )
        self._playbook_loader = PlaybookLoader(
            repository=playbook_repository,
            event_bus=self._event_bus,
            logger=logger,
        )

        # TODO: Register real engine implementations and wire execution pipeline.
        self._engine_registry.register_defaults()

    @property
    def config(self) -> RuntimeConfig:
        """Runtime configuration."""
        return self._config

    @property
    def event_bus(self) -> EventBus:
        """Internal domain event bus."""
        return self._event_bus

    @property
    def case_manager(self) -> CaseManager:
        """Case aggregate manager."""
        return self._case_manager

    @property
    def playbook_loader(self) -> PlaybookLoader:
        """DSL playbook loader."""
        return self._playbook_loader

    @property
    def state_machine(self) -> InvestigationStateMachine:
        """Investigation lifecycle state machine."""
        return self._state_machine

    @property
    def engine_registry(self) -> EngineRegistry:
        """Brain engine registry."""
        return self._engine_registry

    def start(self) -> None:
        """Initialize runtime kernel.

        TODO: Load playbooks index, warm caches, subscribe engine event handlers.
        """
        if self._config.playbooks_path:
            pass  # Future: discover playbooks under playbooks_path

    def shutdown(self) -> None:
        """Gracefully shut down runtime kernel.

        TODO: Flush pending case writes and unsubscribe event handlers.
        """
        self._event_bus.clear()
