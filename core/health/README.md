# Health Rule Framework

Deterministic, vendor-neutral health evaluation for Canonical Voice Objects and voice topology graphs.

## Purpose

Evaluate parser-produced objects and topology relationships using explicit rules — no AI, no vendor-specific logic in the engine layer.

## Layout

| Module | Responsibility |
|--------|----------------|
| `health_severity.py` | `HealthSeverity` enum |
| `health_categories.py` | `HealthCategory` enum |
| `health_models.py` | `HealthStatus`, `HealthResult` |
| `health_rule.py` | `HealthRule` contract |
| `health_rule_registry.py` | Rule registration and lookup |
| `builtin_rules.py` | Built-in v1 rules |
| `health_engine.py` | Evaluation orchestration |
| `health_report.py` | Aggregated report model |

## Usage

```python
from health import HealthEngine

engine = HealthEngine()
report = engine.evaluate_case(case)
report = engine.evaluate_topology(topology)
results = engine.evaluate_object(sip_ua, topology)
```

## Built-in rules (v1)

| Rule ID | Object | Outcome |
|---------|--------|---------|
| `sip_ua_disabled` | SipUA | FAIL when disabled |
| `voice_service_allow_connections_missing` | VoiceService | WARN when policy missing |
| `dial_peer_no_destination_pattern` | DialPeer | FAIL when pattern absent |
| `dial_peer_shutdown` | DialPeer | FAIL when shutdown |
| `provider_no_dependent_dial_peers` | Provider | WARN when no routes_to dial peers |

## Scoring

Start at **100**. Subtract for each WARN/FAIL result:

| Severity | Penalty |
|----------|---------|
| Critical | 30 |
| High | 15 |
| Medium | 10 |
| Low | 5 |
| Info | 0 |

Minimum score: **0**.

## Related

- [Health framework v1 spec](../../docs/sprint-6/health-framework-v1.md)
- [CVOM](../model/README.md)
- [Topology engine](../topology/README.md)
