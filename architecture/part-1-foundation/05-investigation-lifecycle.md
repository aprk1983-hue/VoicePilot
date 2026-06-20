# 05 — Investigation Lifecycle

> **Status:** Implemented

## Purpose

Document the investigation lifecycle from case creation through closure: intake, discovery, analysis, hypothesis, investigation, resolution, verification, learning, and closed states.

## Repository Modules Involved

- [`../../core/runtime/state_machine.py`](../../core/runtime/state_machine.py) — `InvestigationStateMachine`
- [`../../core/runtime/case_manager.py`](../../core/runtime/case_manager.py) — state transitions on `Case`
- [`../../core/domain/enums.py`](../../core/domain/enums.py) — `InvestigationState`
- [`../../core/runtime/intake_flow.py`](../../core/runtime/intake_flow.py) — intake question flow
- [`../../core/runtime/evidence_collection.py`](../../core/runtime/evidence_collection.py) — evidence phase

## Related Tests

- [`../../tests/test_state_machine.py`](../../tests/test_state_machine.py)
- [`../../tests/test_runtime_engine.py`](../../tests/test_runtime_engine.py)
- [`../../tests/test_evidence_collection.py`](../../tests/test_evidence_collection.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)

## Related Documentation

- [`../../docs/sprint-1/runtime-engine-v1.md`](../../docs/sprint-1/runtime-engine-v1.md)
- [`../../docs/sprint-1/evidence-collection-v1.md`](../../docs/sprint-1/evidence-collection-v1.md)
- [`../../docs/product/rfc-001-investigation-engine.md`](../../docs/product/rfc-001-investigation-engine.md)

## Mermaid Diagrams Required

- **Investigation state machine** — `InvestigationState` transitions
- **End-to-end lifecycle flow** — intake through closed case and report

## Cross References

- [03 — Investigation Domain Model](03-investigation-domain-model.md)
- [06 — VoicePilot DSL](06-voicepilot-dsl.md)
- [Part 2 — State and Events](../part-2-architecture/05-state-and-events.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
