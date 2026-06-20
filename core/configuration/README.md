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

## Usage

```python
from configuration import SnapshotEngine, DiffEngine, format_diff_report_markdown
from health import HealthEngine
from knowledge import KnowledgeEngine

topology = TopologyBuilder().build(voice_objects)
health_report = HealthEngine().evaluate_topology(topology)
knowledge_report = KnowledgeEngine().evaluate_topology(topology)

snapshot_engine = SnapshotEngine()
before = snapshot_engine.create_snapshot(topology, health_report, knowledge_report)

diff_engine = DiffEngine()
diff = diff_engine.compare(before, after)
print(format_diff_report_markdown(diff))
```

## Design principles

- Immutable frozen dataclasses
- Deterministic ordering and hashing
- No persistence in Sprint 8.1
- Vendor-neutral CVOM content only

## Related

- [Configuration snapshot v1](../../docs/sprint-8/configuration-snapshot-v1.md)
- [Configuration diff v1](../../docs/sprint-8/configuration-diff-v1.md)
- [CVOM v1](../../docs/sprint-4/canonical-voice-object-model.md)
