# Call Path Engine v1

Sprint 5.4 adds deterministic call path modeling over the voice topology dependency graph.

## Goals

- Model call paths between topology objects using existing dependency paths
- Represent each hop with health metadata and relationship context
- Detect breakpoint candidates from parser-derived object state
- No AI, API, React, or persistence changes

## Package layout

```
core/topology/
  call_path_models.py
  call_path_engine.py
```

## Models

### CallPathDirection

| Value | Meaning |
|-------|---------|
| `outbound` | Off-net or provider-bound call path |
| `inbound` | Inbound call path |
| `internal` | On-net internal path |
| `unknown` | Direction not specified |

### CallPathHop

Each hop captures one object along the path:

| Field | Description |
|-------|-------------|
| `object_id` | CVOM object identifier |
| `object_type` | Canonical object type |
| `label` | Display name |
| `relationship_to_next` | Edge type to the next hop |
| `health_status` | Derived operational status |
| `findings` | Health-related finding tokens |
| `metadata` | Supporting health metadata snapshot |

### CallPath

| Field | Description |
|-------|-------------|
| `id` | Deterministic path identifier |
| `direction` | Path direction |
| `source_object_id` | Origin object |
| `destination_object_id` | Target object |
| `hops` | Ordered hop chain |
| `summary` | Human-readable summary |
| `warnings` | Non-fatal path warnings |

## CallPathEngine

```python
from topology import CallPathEngine, CallPathDirection

engine = CallPathEngine()
path = engine.build_path(
    topology,
    dial_peer_id,
    provider_id,
    direction=CallPathDirection.OUTBOUND,
)
outbound_paths = engine.build_outbound_paths(topology)
breakpoints = engine.find_breakpoints(path)
```

### build_path

Uses `DependencyEngine.explain_dependency_path()` from source to destination. Each relationship is converted into ordered `CallPathHop` entries. If no path exists, returns an empty hop list with warnings instead of raising.

### build_outbound_paths

Builds outbound paths for every dial peer with a `routes_to` relationship to a provider. Results are sorted deterministically by source and destination IDs.

### find_breakpoints

v1 breakpoint rules:

- Inspect hop health metadata from typed CVOM fields and object metadata
- Mark hops unhealthy when status/findings contain `disabled`, `down`, `failed`, or `unregistered`
- If no hop contains health metadata, return an empty breakpoint list

## Example

For VP-CUBE-0001:

```
DialPeer --routes_to--> Provider
DialPeer --uses--> VoiceService --uses--> SipUA
```

`build_path(dial_peer, provider)` yields a two-hop outbound path. `build_path(dial_peer, sip_ua)` yields the full service chain. A disabled SIP-UA hop is flagged by `find_breakpoints()`.

## Testing

```bash
pytest tests/test_call_path_engine.py
```

## Related

- [Dependency engine v1](./dependency-engine-v1.md)
- [Impact analysis v1](./impact-analysis-v1.md)
- [Topology package README](../../core/topology/README.md)
