# Health Rule Framework v1

Sprint 6.1 introduces a deterministic, vendor-neutral health evaluation framework for Canonical Voice Objects and voice topology graphs.

## Goals

- Evaluate object and topology health using explicit rules
- Produce scored reports with category and severity aggregation
- Support future plugin-provided rules through a registry
- No AI, API, React, or persistence changes

## Architecture

```
Case.voice_objects
      ↓
TopologyBuilder → VoiceTopology
      ↓
HealthRuleRegistry → applicable HealthRule set
      ↓
HealthEngine.evaluate_*()
      ↓
HealthReport
```

The engine is rule-driven: each rule inspects typed CVOM fields and optional topology context, then returns a `HealthResult`.

## Core models

### HealthSeverity

`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### HealthCategory

`CONFIGURATION`, `SIP`, `ROUTING`, `SECURITY`, `TLS`, `MEDIA`, `PROVIDER`, `DIAL_PLAN`, `PERFORMANCE`, `HIGH_AVAILABILITY`, `GENERAL`

### HealthStatus

`PASS`, `WARN`, `FAIL`, `UNKNOWN`

### HealthRule

| Field | Purpose |
|-------|---------|
| `id` | Stable rule identifier |
| `title` | Short name |
| `description` | Rule intent |
| `category` | Report grouping |
| `severity` | Score impact |
| `supported_object_types` | Applicable CVOM types |
| `evaluate(object, topology)` | Deterministic evaluation |

### HealthReport

| Field | Purpose |
|-------|---------|
| `overall_score` | 0–100 health score |
| `pass_count` / `warn_count` / `fail_count` | Status totals |
| `category_counts` | Active findings by category |
| `severity_counts` | Active findings by severity |
| `results` | Ordered rule results |
| `recommendations` | Deduplicated remediation guidance |

## Rule lifecycle

1. Define a `HealthRule` subclass or dataclass implementing `evaluate()`
2. Register it with `HealthRuleRegistry.register()`
3. `HealthEngine` selects rules by `supported_object_types`
4. Results are aggregated into a `HealthReport`

Built-in rules ship through `default_health_rule_registry()`.

## Built-in rules (v1)

| Rule | Trigger | Status | Severity |
|------|---------|--------|----------|
| `sip_ua_disabled` | `SipUA.enabled is False` | FAIL | CRITICAL |
| `voice_service_allow_connections_missing` | `allow_connections is None` | WARN | MEDIUM |
| `dial_peer_no_destination_pattern` | empty destination pattern | FAIL | HIGH |
| `dial_peer_shutdown` | `shutdown is True` | FAIL | HIGH |
| `provider_no_dependent_dial_peers` | no `routes_to` dial peers | WARN | LOW |

## Health score

Start at **100**. For each WARN or FAIL result, subtract:

| Severity | Penalty |
|----------|---------|
| Critical | 30 |
| High | 15 |
| Medium | 10 |
| Low | 5 |
| Info | 0 |

Floor at **0**.

## Engine API

```python
from health import HealthEngine

engine = HealthEngine()
object_results = engine.evaluate_object(sip_ua, topology)
topology_report = engine.evaluate_topology(topology)
case_report = engine.evaluate_case(case)
```

## Future plugin rules

Vendor packs can register additional rules without modifying core engine code:

```python
from health import HealthEngine, HealthRuleRegistry
from health.builtin_rules import register_builtin_rules

registry = HealthRuleRegistry()
register_builtin_rules(registry)
registry.register(MyVendorRule())

engine = HealthEngine(registry=registry)
```

Plugin rules should:

- Use vendor-neutral categories where possible
- Avoid guessing when required fields are absent (`UNKNOWN` or PASS)
- Keep evaluation deterministic and side-effect free

## Testing

```bash
pytest tests/test_health_engine.py
```

## Related

- [Health package README](../../core/health/README.md)
- [CVOM v1](../sprint-4/canonical-voice-object-model.md)
- [Topology builder v1](../sprint-5/topology-builder-v1.md)
