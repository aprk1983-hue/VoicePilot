"""Tests for EventBus."""

from __future__ import annotations

from domain.enums import DomainEventType
from domain.events import DomainEvent


class TestEventBus:
    def test_subscribe_and_publish(self, event_bus) -> None:
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        event_bus.subscribe(DomainEventType.CASE_CREATED, handler)
        event = DomainEvent.create(DomainEventType.CASE_CREATED, {"case_id": "CASE-1"})
        event_bus.publish(event)
        assert len(received) == 1
        assert received[0].payload["case_id"] == "CASE-1"

    def test_unsubscribe_removes_handler(self, event_bus) -> None:
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        event_bus.subscribe(DomainEventType.CASE_UPDATED, handler)
        event_bus.unsubscribe(DomainEventType.CASE_UPDATED, handler)
        event_bus.publish(DomainEvent.create(DomainEventType.CASE_UPDATED))
        assert received == []

    def test_multiple_handlers(self, event_bus) -> None:
        counts = {"a": 0, "b": 0}

        def handler_a(_: DomainEvent) -> None:
            counts["a"] += 1

        def handler_b(_: DomainEvent) -> None:
            counts["b"] += 1

        event_bus.subscribe(DomainEventType.CASE_SAVED, handler_a)
        event_bus.subscribe(DomainEventType.CASE_SAVED, handler_b)
        event_bus.publish(DomainEvent.create(DomainEventType.CASE_SAVED))
        assert counts == {"a": 1, "b": 1}

    def test_subscriber_count(self, event_bus) -> None:
        def handler(_: DomainEvent) -> None:
            pass

        event_bus.subscribe(DomainEventType.ENGINE_REGISTERED, handler)
        assert event_bus.subscriber_count(DomainEventType.ENGINE_REGISTERED) == 1
