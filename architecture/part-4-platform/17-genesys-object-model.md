# 17 — Genesys Cloud Object Model

> **Status:** Implemented

## Purpose

Document the Genesys Voice Object Model (GVOM) and deterministic evidence parser framework for Genesys Cloud CX exports.

## Repository Modules Involved

- [`../../core/model/genesys_objects.py`](../../core/model/genesys_objects.py) — 20 frozen GVOM dataclasses
- [`../../core/model/voice_graph.py`](../../core/model/voice_graph.py) — `OBJECT_TYPE_GENESYS_*` constants
- [`../../core/model/voice_topology.py`](../../core/model/voice_topology.py) — Genesys topology buckets
- [`../../plugins/genesys/parser/cloud/`](../../plugins/genesys/parser/cloud/) — export evidence parsers
- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py) — object partitioning
- [`../../core/topology/relationship_builder.py`](../../core/topology/relationship_builder.py) — GVOM relationship rules
- [`../../core/runtime/parser_bootstrap.py`](../../core/runtime/parser_bootstrap.py) — parser registration

## Pipeline Diagram

```text
Genesys Cloud Export Evidence → GenesysCloudParser → GVOM
  → TopologyBuilder → RelationshipBuilder → VoiceTopology
```

## Object Flow

```text
CSV / JSON / YAML / TXT exports
  → parse_genesys_evidence → dedupe_records → validate
  → extract_voice_objects → GVOM (Queue, Agent, EdgeDevice, Flow, ...)
  → TopologyBuilder buckets → RelationshipBuilder edges
```

## Evidence Flow

```text
organization-export / users-export / queues-export / queue-members-export
  / agents-export / presence-export / flows-export / architect-export
  / data-actions-export / byoc-cloud-trunks-export / byoc-premises-trunks-export
  / edge-devices-export / recording-policies-export / campaigns-export / skills-export
  → Parser signals → Future investigation engine (Sprint 14.3+)
```

## Relationship Flow

```text
Agent.queue_id → Queue
Queue.queue_id ← QueueMember
Flow.target_queue → Queue
ArchitectFlow.data_action_id → DataAction
Campaign.queue_id → Queue
ByocPremisesTrunk.edge_id → EdgeDevice
EdgeDevice.organization_id → GenesysOrganization
```

## Sample Evidence

`examples/sample_evidence/genesys/` — healthy, failure, and mixed golden exports.

## Constraints

- Read-only evidence parsing
- No OAuth, REST API, GraphQL, or live tenant connectivity
- Vendor-specific logic in Genesys modules only

## Related Tests

- [`../../tests/test_genesys_parser_framework.py`](../../tests/test_genesys_parser_framework.py)

## Related Documentation

- [`../../docs/sprint-14/genesys-parser-framework-v1.md`](../../docs/sprint-14/genesys-parser-framework-v1.md)
- [`16-genesys-cloud-knowledge-library.md`](16-genesys-cloud-knowledge-library.md)
