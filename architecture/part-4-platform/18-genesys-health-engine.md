# 18 — Genesys Cloud Health Engine

> **Status:** Implemented

## Purpose

Document the Genesys Cloud Health Rules framework: deterministic health evaluation over GVOM objects and topology.

## Repository Modules Involved

- [`../../core/health/genesys_rules.py`](../../core/health/genesys_rules.py) — Genesys health rules
- [`../../core/health/health_engine.py`](../../core/health/health_engine.py) — health evaluation engine
- [`../../core/health/builtin_rules.py`](../../core/health/builtin_rules.py) — rule registration bootstrap
- [`../../core/model/genesys_objects.py`](../../core/model/genesys_objects.py) — GVOM types
- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py) — topology assembly

## Pipeline

```text
Genesys Parser Evidence → GVOM Objects → TopologyBuilder → HealthEngine → HealthReport
```

## Rule Coverage

27 deterministic rules across:

- Authentication
- Users / Agents
- Queues
- Voice Routing (BYOC, SIP, TLS)
- Architect / Data Actions
- Media / Recording / WebRTC
- Campaigns
- Infrastructure (Edge, platform services)

## Constraints

- Read-only evaluation
- No recommendations, hypotheses, or remediation
- Vendor-specific logic contained in `genesys_rules.py`
- No OAuth, REST API, GraphQL, or live Genesys connectivity

## Runtime Integration

`HealthEngine.evaluate_case()` and `evaluate_topology()` automatically include Genesys rules when GVOM objects are present.

## Related Tests

- [`../../tests/test_genesys_health_rules.py`](../../tests/test_genesys_health_rules.py)

## Related Documentation

- [`../../docs/sprint-14/genesys-health-rules-v1.md`](../../docs/sprint-14/genesys-health-rules-v1.md)
- [17 — Genesys Cloud Object Model](17-genesys-object-model.md)

## Cross References

- [16 — Genesys Cloud CX Knowledge Library](16-genesys-cloud-knowledge-library.md)
- [14 — AudioCodes SBC Health Engine](14-audiocodes-health-engine.md)
