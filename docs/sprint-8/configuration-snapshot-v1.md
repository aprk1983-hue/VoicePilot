# Configuration Snapshot v1

Sprint 8.1 introduces the Configuration Snapshot Framework — a deterministic, vendor-neutral way to capture the complete canonical voice topology at a point in time.

## Goals

- Capture immutable topology snapshots
- Attach health and knowledge evaluation context
- Generate deterministic content hashes
- Provide in-memory storage for Sprint 8.1
- Enable future diffing, drift detection, and baselines

**Not in v1:**

- Database persistence
- Diff engine
- API or UI integration
- AI analysis

## Architecture

```
VoiceTopology
HealthReport
KnowledgeReport
      ↓
SnapshotBuilder
      ↓
ConfigurationSnapshot
      ↓
SnapshotStorage (in-memory)
      ↓
SnapshotEngine
      ↓
SnapshotReport
```

## ConfigurationSnapshot

| Field | Purpose |
|-------|---------|
| `snapshot_id` | Stable snapshot identifier (`SNAP-*`) |
| `timestamp` | Capture time (UTC) |
| `hostname` | Primary device hostname |
| `vendor` / `platform` | Scope metadata |
| `software_version` | Platform software version |
| `voice_objects` | Canonical CVOM objects |
| `relationships` | Typed topology relationships |
| `health_report` | Health evaluation at capture time |
| `knowledge_report` | Knowledge matches at capture time |
| `metadata` | Additional capture metadata |
| `snapshot_hash` | Deterministic SHA256 content hash |

## Hashing

`compute_snapshot_hash()` canonicalizes voice objects and relationships with stable ordering before SHA256 hashing. Object input order does not affect the hash.

## Engine API

```python
from configuration import SnapshotEngine

engine = SnapshotEngine()
snapshot = engine.create_snapshot(topology, health_report, knowledge_report)
report = engine.evaluate_snapshot(snapshot.snapshot_id)
all_snapshots = engine.list_snapshots()
```

## Snapshot lifecycle

1. Build topology from parsed voice objects
2. Evaluate health and knowledge reports
3. Create immutable snapshot via `SnapshotEngine.create_snapshot()`
4. Store in memory via `SnapshotStorage`
5. Summarize via `evaluate_snapshot()`

## Future Diff Engine

Snapshots are designed as the foundation for:

- Configuration diff between two capture points
- Drift detection against approved baselines
- Historical topology analysis across investigations
- Change validation before/after maintenance windows

The content hash enables quick equality checks before deeper structural diffing.

## Tests

```bash
pytest tests/test_snapshot_engine.py -v
```

## Related

- [Configuration package README](../../core/configuration/README.md)
- [Health framework v1](../sprint-6/health-framework-v1.md)
- [Knowledge framework v1](../sprint-7/knowledge-framework-v1.md)
- [Topology relationship engine v1](../sprint-5/topology-relationship-engine-v1.md)
