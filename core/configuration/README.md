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

## Usage

```python
from configuration import SnapshotEngine
from health import HealthEngine
from knowledge import KnowledgeEngine

topology = TopologyBuilder().build(voice_objects)
health_report = HealthEngine().evaluate_topology(topology)
knowledge_report = KnowledgeEngine().evaluate_topology(topology)

engine = SnapshotEngine()
snapshot = engine.create_snapshot(topology, health_report, knowledge_report)
report = engine.evaluate_snapshot(snapshot.snapshot_id)
```

## Design principles

- Immutable frozen dataclasses
- Deterministic ordering and hashing
- No persistence in Sprint 8.1
- Vendor-neutral CVOM content only

## Related

- [Configuration snapshot v1](../../docs/sprint-8/configuration-snapshot-v1.md)
- [CVOM v1](../../docs/sprint-4/canonical-voice-object-model.md)
