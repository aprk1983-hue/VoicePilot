# Impact Analysis Engine v1

Sprint 5.3 adds deterministic operational impact prediction over the voice topology dependency graph.

## Goals

- Predict blast radius when an object fails, is removed, or is reconfigured
- Derive impact only from graph relationships — never guess
- Reuse `DependencyEngine` for transitive dependent traversal
- No AI, API, React, or persistence changes

## Package layout

```
core/topology/
  impact_models.py
  impact_engine.py
```

## Models

### ImpactSeverity

| Dependent count | Severity |
|-----------------|----------|
| 0 | `LOW` |
| 1–2 | `MEDIUM` |
| 3–5 | `HIGH` |
| 6+ | `CRITICAL` |

Counts are based on transitive dependents returned by `DependencyEngine.get_transitive_dependents()`.

### ImpactReport

| Field | Description |
|-------|-------------|
| `affected_object` | Object being analyzed |
| `severity` | Graph-derived severity |
| `impacted_objects` | Transitive dependents (sorted by ID) |
| `dependency_paths` | Shortest path from each impacted object to the affected object |
| `summary` | Deterministic human-readable summary |
| `recommendations` | Type-specific operational guidance |

## ImpactEngine

```python
from topology import ImpactEngine

engine = ImpactEngine()
report = engine.analyze_failure(topology, sip_ua_id)
report = engine.analyze_removal(topology, voice_service_id)
report = engine.analyze_configuration_change(topology, dial_peer_id)
```

Each method:

1. Resolves the affected object in the topology
2. Calls `DependencyEngine.get_transitive_dependents()`
3. Builds dependency paths with `explain_dependency_path()`
4. Applies severity thresholds and type-specific recommendations

## Recommendations (v1)

| Object type | Recommendation |
|-------------|----------------|
| `sip_ua` | Validate SIP registration after change. |
| `voice_service` | Verify all outbound dial peers. |
| `dial_peer` | Perform outbound PSTN test. |
| `provider` | Verify all associated trunks. |

Other object types return no recommendations unless extended in a future sprint.

## Example

For a VP-CUBE-0001 chain:

```
DialPeer --uses--> VoiceService --uses--> SipUA --binds_to--> Interface
DialPeer --routes_to--> Provider
```

Analyzing SIP-UA failure yields:

- **Severity:** `MEDIUM` (voice service + dial peer depend on it)
- **Impacted objects:** voice service, dial peer
- **Paths:** dial peer → voice service → SIP-UA; voice service → SIP-UA

## Testing

```bash
pytest tests/test_impact_engine.py
```

## Related

- [Dependency engine v1](./dependency-engine-v1.md)
- [Topology builder v1](./topology-builder-v1.md)
