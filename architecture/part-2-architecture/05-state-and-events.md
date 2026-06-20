# 05 — State and Events

> **Status:** Implemented

## Purpose

Document the investigation state machine, valid transitions, domain events, and the in-process event bus used during runtime execution.

## Repository Modules Involved

- [`../../core/runtime/state_machine.py`](../../core/runtime/state_machine.py) — `InvestigationStateMachine`
- [`../../core/runtime/event_bus.py`](../../core/runtime/event_bus.py) — `EventBus`
- [`../../core/domain/events.py`](../../core/domain/events.py) — typed domain events
- [`../../core/domain/enums.py`](../../core/domain/enums.py) — `InvestigationState`, `DomainEventType`

## Related Tests

- [`../../tests/test_state_machine.py`](../../tests/test_state_machine.py)
- [`../../tests/test_event_bus.py`](../../tests/test_event_bus.py)

## Related Documentation

- [`../../docs/product/case-state-model.md`](../../docs/product/case-state-model.md)
- [`../../brain/state-machine/README.md`](../../brain/state-machine/README.md) — planned brain doc (not implemented code)

## Mermaid Diagrams Required

- **State transition diagram** — all `InvestigationState` values and guards
- **Event bus publish/subscribe flow** — domain events during investigation

## Cross References

- [Part 1 — Investigation Lifecycle](../part-1-foundation/05-investigation-lifecycle.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
