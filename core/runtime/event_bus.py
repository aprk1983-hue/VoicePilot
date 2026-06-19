"""Lightweight in-process event bus for domain events."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, List

from domain.enums import DomainEventType
from domain.events import DomainEvent
from domain.interfaces import EventBusPort, EventHandler, LoggerPort


class EventBus(EventBusPort):
    """Synchronous internal event bus.

    Handlers are invoked in registration order. No external messaging.
    """

    def __init__(self, logger: LoggerPort | None = None) -> None:
        self._handlers: DefaultDict[DomainEventType, List[EventHandler]] = defaultdict(list)
        self._logger = logger

    def subscribe(self, event_type: DomainEventType, handler: EventHandler) -> None:
        """Register ``handler`` for ``event_type``."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: DomainEventType, handler: EventHandler) -> None:
        """Remove ``handler`` from ``event_type`` subscribers."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """Dispatch ``event`` to all subscribers of its type."""
        if self._logger:
            self._logger.debug(
                "Publishing domain event",
                event_type=event.event_type.name,
                event_id=event.event_id,
            )
        for handler in list(self._handlers[event.event_type]):
            handler(event)

    def clear(self) -> None:
        """Remove all subscribers. Intended for tests."""
        self._handlers.clear()

    def subscriber_count(self, event_type: DomainEventType) -> int:
        """Return number of handlers for ``event_type``."""
        return len(self._handlers.get(event_type, []))
