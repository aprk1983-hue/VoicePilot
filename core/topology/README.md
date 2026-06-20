# Voice Topology Engine

Deterministic, vendor-neutral graph builder that connects Canonical Voice Objects (CVOM) into a relationship topology.

## Purpose

Parsers attach typed objects to a case. The topology engine reads those objects and infers explicit relationships without guessing or mutating source data.

## Layout

| Module | Responsibility |
|--------|----------------|
| `relationship_types.py` | `RelationshipType` enum |
| `relationship_builder.py` | Rule-based relationship inference |
| `topology_builder.py` | Assembles immutable `VoiceTopology` |
| `topology_exceptions.py` | Topology build errors |

## v1 rules

| Rule | Source | Type | Target | Condition |
|------|--------|------|--------|-----------|
| 1 | `DialPeer` | `USES` | `VoiceService` | Exactly one voice service |
| 2 | `VoiceService` | `USES` | `SipUA` | Exactly one voice service and one SIP-UA |
| 3 | `SipUA` | `BINDS_TO` | `Interface` | Interface exists on same hostname |
| 4 | `DialPeer` | `ROUTES_TO` | `Provider` | Provider exists (single provider, or session target match) |

Missing objects or ambiguous multiples omit the relationship.

## Usage

```python
from topology import TopologyBuilder

topology = TopologyBuilder().build(case.voice_objects)
```

## Related

- [CVOM](../model/README.md)
- [Topology builder v1 spec](../../docs/sprint-5/topology-builder-v1.md)
