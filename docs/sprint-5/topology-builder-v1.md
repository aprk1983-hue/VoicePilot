# Topology Relationship Engine v1

Sprint 5.1 introduces a vendor-neutral topology engine that connects Canonical Voice Objects (CVOM) into an immutable relationship graph.

## Goals

- Connect parser-produced objects without mutating them
- Apply explicit, deterministic relationship rules only
- Never guess when required objects are missing or ambiguous
- No AI, API, React, persistence, or visualization changes

## Package layout

```
core/topology/
  relationship_types.py
  relationship_builder.py
  topology_builder.py
  topology_exceptions.py
```

## Relationship types

`RelationshipType` defines the v1 edge vocabulary:

| Value | Meaning |
|-------|---------|
| `uses` | Operational dependency |
| `depends_on` | Hard dependency |
| `connects_to` | Network/session connectivity |
| `binds_to` | Control or media binding |
| `routes_to` | Call routing target |
| `hosted_on` | Hosting placement |
| `provides` | Service provision |
| `references` | Configuration reference |
| `translates_to` | Number or policy translation |
| `authenticates_to` | Authentication target |

Only a subset is used in v1 rules; the enum reserves the full vocabulary.

## v1 inference rules

### Rule 1 — DialPeer USES VoiceService

For each dial peer, create a `uses` edge to the voice service when **exactly one** `VoiceService` object is present.

If zero or multiple voice services exist, the rule is skipped.

### Rule 2 — VoiceService USES SipUA

Create a `uses` edge from the voice service to the SIP-UA when **exactly one** `VoiceService` and **exactly one** `SipUA` are present.

### Rule 3 — SipUA BINDS_TO Interface

For each SIP-UA, create `binds_to` edges to interfaces on the **same hostname**.

If no matching interface exists, the rule is skipped for that SIP-UA.

### Rule 4 — DialPeer ROUTES_TO Provider

For each dial peer:

- If exactly one provider exists, route to that provider.
- If multiple providers exist, route only when `session_target` explicitly matches a provider address.
- Otherwise omit the relationship.

## Builders

### RelationshipBuilder

```python
from topology import RelationshipBuilder

relationships = RelationshipBuilder().build(case.voice_objects)
```

Returns a deduplicated tuple of `VoiceRelationship` instances keyed by `(source_id, target_id, type)`.

### TopologyBuilder

```python
from topology import TopologyBuilder

topology = TopologyBuilder().build(case.voice_objects)
```

Returns an immutable `VoiceTopology` containing:

- All partitioned CVOM objects (devices, interfaces, voice services, SIP-UAs, providers, dial peers)
- All inferred relationships

## Output model

`VoiceTopology` (in `core/model/voice_topology.py`) was extended to include `voice_services` and `sip_uas` buckets while preserving existing fields.

## Testing

```bash
pytest tests/test_relationship_builder.py tests/test_topology_builder.py
```

Coverage includes empty graphs, partial chains, duplicate prevention, hostname-scoped interface binding, and relationship counts.

## Related

- [CVOM v1](../sprint-4/canonical-voice-object-model.md)
- [Case voice object registry](../sprint-4/case-voice-object-registry.md)
- [Topology package README](../../core/topology/README.md)
