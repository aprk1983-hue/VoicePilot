# 03 — Investigation Domain Model

> **Status:** Implemented

## Purpose

Document the investigation aggregate (`Case`), supporting entities, value objects, enums, domain events, and repository ports that form the investigation domain layer.

## Repository Modules Involved

- [`../../core/domain/models.py`](../../core/domain/models.py) — `Case`, `Evidence`, `Hypothesis`, `Recommendation`, etc.
- [`../../core/domain/value_objects.py`](../../core/domain/value_objects.py) — `SymptomSummary`, `AffectedScope`, `PlatformRef`
- [`../../core/domain/enums.py`](../../core/domain/enums.py) — `InvestigationState`, `Severity`, etc.
- [`../../core/domain/events.py`](../../core/domain/events.py) — domain events
- [`../../core/domain/interfaces.py`](../../core/domain/interfaces.py) — ports (`CaseRepository`, `PlaybookRepository`, etc.)

## Related Tests

- [`../../tests/test_case_manager.py`](../../tests/test_case_manager.py)
- [`../../tests/test_runtime_engine.py`](../../tests/test_runtime_engine.py)
- [`../../tests/test_voice_object_case_attachment.py`](../../tests/test_voice_object_case_attachment.py)

## Related Documentation

- [`../../docs/data-model/canonical-data-model.md`](../../docs/data-model/canonical-data-model.md)
- [`../../docs/product/case-state-model.md`](../../docs/product/case-state-model.md)
- [`../../docs/product/rfc-001-investigation-engine.md`](../../docs/product/rfc-001-investigation-engine.md)

## Mermaid Diagrams Required

- **Case aggregate diagram** — entities attached to `Case`
- **Investigation entity relationship diagram** — evidence, findings, hypotheses, recommendations

## Cross References

- [05 — Investigation Lifecycle](05-investigation-lifecycle.md)
- [Part 2 — Runtime Kernel](../part-2-architecture/03-runtime-kernel.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
