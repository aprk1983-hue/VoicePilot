# 06 — Configuration Engines

> **Status:** Implemented

## Purpose

Document configuration snapshot capture, deterministic hashing, snapshot diff, approved baselines, and drift detection — all in-memory for the current release.

## Repository Modules Involved

- [`../../core/configuration/snapshot_engine.py`](../../core/configuration/snapshot_engine.py)
- [`../../core/configuration/snapshot_builder.py`](../../core/configuration/snapshot_builder.py)
- [`../../core/configuration/snapshot_hash.py`](../../core/configuration/snapshot_hash.py)
- [`../../core/configuration/diff_engine.py`](../../core/configuration/diff_engine.py)
- [`../../core/configuration/drift_engine.py`](../../core/configuration/drift_engine.py)
- [`../../core/configuration/baseline_registry.py`](../../core/configuration/baseline_registry.py)
- Supporting: `snapshot_registry.py`, `snapshot_storage.py`, `diff_report.py`, `drift_report.py`

## Related Tests

- [`../../tests/test_snapshot_engine.py`](../../tests/test_snapshot_engine.py)
- [`../../tests/test_configuration_diff_engine.py`](../../tests/test_configuration_diff_engine.py)
- [`../../tests/test_baseline_drift_engine.py`](../../tests/test_baseline_drift_engine.py)

## Related Documentation

- [`../../docs/sprint-8/configuration-snapshot-v1.md`](../../docs/sprint-8/configuration-snapshot-v1.md)
- [`../../docs/sprint-8/configuration-diff-v1.md`](../../docs/sprint-8/configuration-diff-v1.md)
- [`../../docs/sprint-8/baseline-drift-v1.md`](../../docs/sprint-8/baseline-drift-v1.md)
- [`../../core/configuration/README.md`](../../core/configuration/README.md)

## Mermaid Diagrams Required

- **Snapshot lifecycle** — topology + reports → snapshot → storage
- **Diff and drift pipeline** — baseline → diff → drift status → recommendations

## Cross References

- [03 — Topology Engines](03-topology-engines.md)
- [04 — Health Engine](04-health-engine.md)
- [05 — Knowledge Framework](05-knowledge-framework.md)
- [Part 5 — Persistence](../part-5-future/04-persistence.md)
