"""Domain ports (interfaces) for hexagonal architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Protocol

from domain.events import DomainEvent
from domain.enums import DomainEventType, InvestigationState
from domain.models import Case, Playbook
from shared.types import CaseId, JsonDict


class CaseRepository(ABC):
    """Persistence port for investigation cases."""

    @abstractmethod
    def save(self, case: Case) -> None:
        """Persist the given case aggregate."""

    @abstractmethod
    def load(self, case_id: CaseId) -> Case:
        """Load a case by identifier."""


class PlaybookRepository(ABC):
    """Port for loading DSL playbook documents."""

    @abstractmethod
    def load_by_path(self, path: Path) -> JsonDict:
        """Load raw playbook document from filesystem path."""


class EventHandler(Protocol):
    """Callable protocol for domain event subscribers."""

    def __call__(self, event: DomainEvent) -> None: ...


class EventBusPort(ABC):
    """Port for internal domain event distribution."""

    @abstractmethod
    def subscribe(self, event_type: DomainEventType, handler: EventHandler) -> None:
        """Register a handler for an event type."""

    @abstractmethod
    def unsubscribe(self, event_type: DomainEventType, handler: EventHandler) -> None:
        """Remove a handler for an event type."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to registered handlers."""


class StateMachinePort(ABC):
    """Port for investigation lifecycle transition validation."""

    @abstractmethod
    def can_transition(self, from_state: InvestigationState, to_state: InvestigationState) -> bool:
        """Return whether the transition is structurally allowed."""

    @abstractmethod
    def allowed_transitions(self, from_state: InvestigationState) -> frozenset[InvestigationState]:
        """Return valid target states from the given state."""


class BrainEngine(Protocol):
    """Marker protocol for registrable brain engines.

    Engines will expose a ``name`` attribute in future implementation sprints.
    """

    name: str


class LoggerPort(ABC):
    """Structured logging port."""

    @abstractmethod
    def info(self, message: str, **context: object) -> None: ...

    @abstractmethod
    def error(self, message: str, **context: object) -> None: ...

    @abstractmethod
    def debug(self, message: str, **context: object) -> None: ...
