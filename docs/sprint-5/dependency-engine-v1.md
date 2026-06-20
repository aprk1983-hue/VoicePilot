# Topology Dependency Engine v1

Sprint 5.2 adds directed dependency traversal over `VoiceTopology` relationship graphs.

## Goals

- Query what an object depends on and what depends on it
- Walk transitive dependency chains with depth limits
- Explain shortest directed paths between objects
- Remain deterministic, cycle-safe, and vendor-neutral
- No AI, API, React, persistence, or visualization changes

## Package layout

```
core/topology/
  dependency_engine.py
  topology_queries.py
```

## DependencyEngine

```python
from topology import DependencyEngine

engine = DependencyEngine()
dependencies = engine.get_direct_dependencies(topology, dial_peer_id)
dependents = engine.get_transitive_dependents(topology, sip_ua_id)
path = engine.explain_dependency_path(topology, dial_peer_id, interface_id)
```

### Methods

| Method | Direction | Description |
|--------|-----------|-------------|
| `get_direct_dependencies` | Outgoing | Targets this object points to |
| `get_direct_dependents` | Incoming | Sources that point to this object |
| `get_transitive_dependencies` | Outgoing BFS | All reachable targets up to `max_depth` |
| `get_transitive_dependents` | Incoming BFS | All reachable sources up to `max_depth` |
| `explain_dependency_path` | Shortest path | Ordered `VoiceRelationship` chain |

### Traversal rules

- Relationships are **directed** (`source` → `target`).
- **Cycles** are prevented with a visited set during traversal.
- Results are returned in **deterministic sorted order** by object ID.
- Missing object IDs raise `TopologyObjectNotFoundError`.
- Unreachable paths return an empty tuple from `explain_dependency_path`.

## TopologyQueries

High-level helpers for common voice topology questions:

| Method | Returns |
|--------|---------|
| `find_dial_peers_using_voice_service` | Dial peers with `uses` → voice service |
| `find_dial_peers_routing_to_provider` | Dial peers with `routes_to` → provider |
| `find_objects_depending_on_sipua` | Transitive dependents of SIP-UA objects |

```python
from topology import TopologyQueries

queries = TopologyQueries()
dial_peers = queries.find_dial_peers_using_voice_service(topology)
dependents = queries.find_objects_depending_on_sipua(topology)
```

## Example chain

For a typical VP-CUBE-0001 topology:

```
DialPeer --uses--> VoiceService --uses--> SipUA --binds_to--> Interface
DialPeer --routes_to--> Provider
```

Transitive dependencies of a dial peer include the voice service, SIP-UA, interface, and provider. Transitive dependents of the SIP-UA include the voice service and dial peer(s).

## Testing

```bash
pytest tests/test_dependency_engine.py tests/test_topology_queries.py
```

## Related

- [Topology builder v1](./topology-builder-v1.md)
- [Topology package README](../../core/topology/README.md)
