# 10 — Microsoft Teams Health Engine

> **Status:** Implemented

## Purpose

Document the Microsoft Teams Health Rules framework: deterministic health evaluation over Teams CVOM objects and topology.

## Repository Modules Involved

- [`../../core/health/teams_rules.py`](../../core/health/teams_rules.py) — Teams health rules
- [`../../core/health/health_engine.py`](../../core/health/health_engine.py) — health evaluation engine
- [`../../core/health/builtin_rules.py`](../../core/health/builtin_rules.py) — rule registration bootstrap
- [`../../core/model/teams_objects.py`](../../core/model/teams_objects.py) — Teams CVOM types
- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py) — topology assembly

## Pipeline

```text
Teams Parser Evidence → CVOM Objects → TopologyBuilder → HealthEngine → HealthReport
```

## Rule Coverage

26 deterministic rules across:

- Licensing
- User configuration
- Voice routing
- Direct Routing
- Operator Connect
- Emergency calling
- Resource accounts

## Constraints

- Read-only evaluation
- No recommendations, hypotheses, or remediation
- Vendor-specific logic contained in `teams_rules.py`
- No Graph API, PowerShell, or Microsoft authentication

## Runtime Integration

`HealthEngine.evaluate_case()` and `evaluate_topology()` automatically include Teams rules when objects are present. Used by:

- CLI health commands
- `ReportEngine`
- `BrainEngine`

## Related Tests

- [`../../tests/test_teams_health_rules.py`](../../tests/test_teams_health_rules.py)

## Related Documentation

- [`../../docs/sprint-12/teams-health-rules-v1.md`](../../docs/sprint-12/teams-health-rules-v1.md)
- [09 — Microsoft Teams Parser Pipeline](09-microsoft-teams-parser-pipeline.md)

## Cross References

- [02 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [03 — Topology Engines](../part-3-engines/03-topology-engines.md)
