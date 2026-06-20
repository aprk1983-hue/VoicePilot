# Configuration Snapshot Framework

Sprint 8.1 introduces immutable, vendor-neutral configuration snapshots of canonical voice topology at a point in time.

## Components

| Module | Purpose |
|--------|---------|
| `snapshot_models.py` | `ConfigurationSnapshot` data model |
| `snapshot_builder.py` | Build snapshots from topology + reports |
| `snapshot_hash.py` | Deterministic SHA256 content hash |
| `snapshot_registry.py` | Register and lookup snapshots |
| `snapshot_storage.py` | In-memory storage (Sprint 8.1) |
| `snapshot_engine.py` | Create, list, get, evaluate API |
| `snapshot_report.py` | Snapshot summary report |
| `snapshot_exceptions.py` | Duplicate/not-found errors |
| `diff_models.py` | Diff change types and result models |
| `diff_engine.py` | Compare snapshots and objects |
| `diff_report.py` | Markdown diff report formatting |
| `baseline_models.py` | Baseline and drift result models |
| `baseline_registry.py` | Approved baseline registry |
| `drift_engine.py` | Compare snapshots against baselines |
| `drift_report.py` | Markdown drift report formatting |

## Usage

```python
from configuration import (
    BaselineRegistry,
    DriftEngine,
    SnapshotEngine,
    format_drift_report_markdown,
)
from health import HealthEngine
from knowledge import KnowledgeEngine

topology = TopologyBuilder().build(voice_objects)
health_report = HealthEngine().evaluate_topology(topology)
knowledge_report = KnowledgeEngine().evaluate_topology(topology)

snapshot_engine = SnapshotEngine()
baseline_snapshot = snapshot_engine.create_snapshot(
    topology,
    health_report,
    knowledge_report,
)

registry = BaselineRegistry()
baseline = registry.register_baseline(
    baseline_snapshot,
    approved_by="ops-lead",
    label="Approved CUBE baseline",
)

drift_engine = DriftEngine(baseline_registry=registry)
report = drift_engine.compare_to_latest_baseline(current_snapshot, "cube-edge-01")
print(format_drift_report_markdown(report))
```

## Design principles

- Immutable frozen dataclasses
- Deterministic ordering and hashing
- No persistence in Sprint 8.1
- Vendor-neutral CVOM content only

## Related

- [Configuration snapshot v1](../../docs/sprint-8/configuration-snapshot-v1.md)
- [Configuration diff v1](../../docs/sprint-8/configuration-diff-v1.md)
- [Baseline and drift v1](../../docs/sprint-8/baseline-drift-v1.md)
- [CVOM v1](../../docs/sprint-4/canonical-voice-object-model.md)
