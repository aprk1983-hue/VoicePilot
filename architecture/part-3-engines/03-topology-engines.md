# 03 — Topology Engines

> **Status:** Implemented

## Purpose

Document voice topology construction, relationship inference, dependency traversal, impact analysis, call path modeling, and topology query helpers.

## Repository Modules Involved

- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py)
- [`../../core/topology/relationship_builder.py`](../../core/topology/relationship_builder.py)
- [`../../core/topology/dependency_engine.py`](../../core/topology/dependency_engine.py)
- [`../../core/topology/impact_engine.py`](../../core/topology/impact_engine.py)
- [`../../core/topology/call_path_engine.py`](../../core/topology/call_path_engine.py)
- [`../../core/topology/topology_queries.py`](../../core/topology/topology_queries.py)
- [`../../core/model/voice_topology.py`](../../core/model/voice_topology.py)

## Related Tests

- [`../../tests/test_topology_builder.py`](../../tests/test_topology_builder.py)
- [`../../tests/test_relationship_builder.py`](../../tests/test_relationship_builder.py)
- [`../../tests/test_dependency_engine.py`](../../tests/test_dependency_engine.py)
- [`../../tests/test_impact_engine.py`](../../tests/test_impact_engine.py)
- [`../../tests/test_call_path_engine.py`](../../tests/test_call_path_engine.py)
- [`../../tests/test_topology_queries.py`](../../tests/test_topology_queries.py)

## Related Documentation

- [`../../docs/sprint-5/topology-builder-v1.md`](../../docs/sprint-5/topology-builder-v1.md)
- [`../../docs/sprint-5/dependency-engine-v1.md`](../../docs/sprint-5/dependency-engine-v1.md)
- [`../../docs/sprint-5/impact-analysis-v1.md`](../../docs/sprint-5/impact-analysis-v1.md)
- [`../../docs/sprint-5/call-path-engine-v1.md`](../../docs/sprint-5/call-path-engine-v1.md)
- [`../../docs/sprint-5/call-path-reporting-v1.md`](../../docs/sprint-5/call-path-reporting-v1.md)

## Mermaid Diagrams Required

- **Topology build pipeline** — CVOM objects → relationships → `VoiceTopology`
- **Call path graph** — outbound path from dial peer to provider
- **Dependency traversal** — directed dependency edges

## Cross References

- [Part 1 — Canonical Voice Object Model](../part-1-foundation/04-canonical-voice-object-model.md)
- [04 — Health Engine](04-health-engine.md)
- [07 — Report Engine](07-report-engine.md)
