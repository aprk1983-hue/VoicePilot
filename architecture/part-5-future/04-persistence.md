# 04 — Persistence

> **Status:** Planned

## Purpose

Document the current in-memory persistence model and future durable storage needs for cases, snapshots, baselines, and audit logs.

## Repository Modules Involved

**Implemented (in-memory only):**

- [`../../core/infrastructure/filesystem.py`](../../core/infrastructure/filesystem.py) — `InMemoryCaseRepository`, filesystem playbook repo
- [`../../core/configuration/snapshot_storage.py`](../../core/configuration/snapshot_storage.py) — in-memory snapshots
- [`../../core/configuration/baseline_registry.py`](../../core/configuration/baseline_registry.py) — in-memory baselines

**Not implemented:**

- No database adapters or ORM modules exist in the repository

## Related Tests

- [`../../tests/test_case_manager.py`](../../tests/test_case_manager.py) — in-memory case repository
- [`../../tests/test_snapshot_engine.py`](../../tests/test_snapshot_engine.py)
- [`../../tests/test_baseline_drift_engine.py`](../../tests/test_baseline_drift_engine.py)

## Related Documentation

- [`../../docs/sprint-8/configuration-snapshot-v1.md`](../../docs/sprint-8/configuration-snapshot-v1.md) — explicitly no persistence in v1
- [`../../docs/sprint-8/baseline-drift-v1.md`](../../docs/sprint-8/baseline-drift-v1.md)

## Mermaid Diagrams Required

- **Current in-memory persistence map** — what is stored only for process lifetime
- **Future persistence architecture** — repositories backed by durable store (planned)

## Cross References

- [Part 3 — Configuration Engines](../part-3-engines/06-configuration-engines.md)
- [Part 1 — Investigation Domain Model](../part-1-foundation/03-investigation-domain-model.md)
