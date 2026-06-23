# 14 — AudioCodes SBC Health Engine

> **Status:** Implemented

## Purpose

Document the AudioCodes SBC Health Rules framework: deterministic health evaluation over AVOM objects and topology.

## Repository Modules Involved

- [`../../core/health/audiocodes_rules.py`](../../core/health/audiocodes_rules.py) — AudioCodes health rules
- [`../../core/health/health_engine.py`](../../core/health/health_engine.py) — health evaluation engine
- [`../../core/health/builtin_rules.py`](../../core/health/builtin_rules.py) — rule registration bootstrap
- [`../../core/model/audiocodes_objects.py`](../../core/model/audiocodes_objects.py) — AVOM types
- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py) — topology assembly

## Pipeline

```text
AudioCodes Parser Evidence → AVOM Objects → TopologyBuilder → HealthEngine → HealthReport
```

## Rule Coverage

25 deterministic rules across:

- SIP / signaling
- SBC configuration
- TLS / security
- Media
- HA / licensing
- Network

## Constraints

- Read-only evaluation
- No recommendations, hypotheses, or remediation
- Vendor-specific logic contained in `audiocodes_rules.py`
- No SSH, REST API, or AudioCodes connectivity

## Runtime Integration

`HealthEngine.evaluate_case()` and `evaluate_topology()` automatically include AudioCodes rules when objects are present.

## Related Tests

- [`../../tests/test_audiocodes_health_rules.py`](../../tests/test_audiocodes_health_rules.py)

## Related Documentation

- [`../../docs/sprint-13/audiocodes-health-rules-v1.md`](../../docs/sprint-13/audiocodes-health-rules-v1.md)
- [13 — AudioCodes SBC Object Model](13-audiocodes-object-model.md)

## Cross References

- [12 — AudioCodes SBC Knowledge Library](12-audiocodes-knowledge-library.md)
- [10 — Microsoft Teams Health Engine](10-microsoft-teams-health-engine.md)
