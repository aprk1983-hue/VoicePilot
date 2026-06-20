# Voice Topology Engine

Deterministic, vendor-neutral graph builder and query layer for Canonical Voice Objects (CVOM).

## Purpose

Parsers attach typed objects to a case. The topology engine reads those objects, infers explicit relationships, and supports dependency traversal without guessing or mutating source data.

## Layout

| Module | Responsibility |
|--------|----------------|
| `relationship_types.py` | `RelationshipType` enum |
| `relationship_builder.py` | Rule-based relationship inference |
| `topology_builder.py` | Assembles immutable `VoiceTopology` |
| `dependency_engine.py` | Directed dependency traversal |
| `topology_queries.py` | High-level topology queries |
| `impact_models.py` | Impact severity and report models |
| `impact_engine.py` | Failure/removal/change impact analysis |
| `call_path_models.py` | Call path hop and path models |
| `call_path_engine.py` | Deterministic call path modeling |
| `topology_exceptions.py` | Topology build and lookup errors |

## Relationship rules (v1)

| Rule | Source | Type | Target | Condition |
|------|--------|------|--------|-----------|
| 1 | `DialPeer` | `USES` | `VoiceService` | Exactly one voice service |
| 2 | `VoiceService` | `USES` | `SipUA` | Exactly one voice service and one SIP-UA |
| 3 | `SipUA` | `BINDS_TO` | `Interface` | Interface exists on same hostname |
| 4 | `DialPeer` | `ROUTES_TO` | `Provider` | Provider exists (single provider, or session target match) |

Missing objects or ambiguous multiples omit the relationship.

## Usage

Build a topology from case voice objects:

```python
from topology import TopologyBuilder

topology = TopologyBuilder().build(case.voice_objects)
```

Traverse dependencies:

```python
from topology import DependencyEngine, TopologyQueries

engine = DependencyEngine()
dependencies = engine.get_transitive_dependencies(topology, dial_peer_id)
path = engine.explain_dependency_path(topology, dial_peer_id, sip_ua_id)

queries = TopologyQueries()
dial_peers = queries.find_dial_peers_using_voice_service(topology)

impact = ImpactEngine().analyze_failure(topology, sip_ua_id)

call_paths = CallPathEngine().build_outbound_paths(topology)
```

## Related

- [CVOM](../model/README.md)
- [Topology builder v1 spec](../../docs/sprint-5/topology-builder-v1.md)
- [Dependency engine v1 spec](../../docs/sprint-5/dependency-engine-v1.md)
- [Impact analysis v1 spec](../../docs/sprint-5/impact-analysis-v1.md)
- [Call path engine v1 spec](../../docs/sprint-5/call-path-engine-v1.md)
