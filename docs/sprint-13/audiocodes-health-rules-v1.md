# AudioCodes SBC Health Rules v1

## Purpose

Sprint 13.3 introduces deterministic AudioCodes SBC health rules that evaluate AVOM objects produced by the Sprint 13.2 parser framework.

Rules are read-only: no SSH, REST API, AudioCodes connectivity, recommendations, hypotheses, or remediation.

## Architecture

```text
AudioCodes AVOM Objects + VoiceTopology
        │
        ▼
HealthEngine (AudioCodes HealthRules)
        │
        ▼
HealthReport (HealthResult findings + score)
```

## Rule Categories

| Category | Rules |
|----------|-------|
| SIP / Signaling | SIP OPTIONS failed, Provider 503, 408 timeout, 403 forbidden, 488 codec mismatch |
| SBC Configuration | Proxy Set unavailable, IP Group disabled, SIP Interface down, Routing Rule missing, Manipulation Set missing |
| TLS / Security | TLS certificate expired, TLS context missing, TLS negotiation failure, SIP flood protection, DoS protection |
| Media | Media Realm missing, Media Realm down, RTP one-way audio, SRTP mismatch |
| HA / Licensing | HA standby not synchronized, HA failover active, Session license exhausted, SBC license invalid |
| Network | Gateway unreachable, DNS resolution failure |

## Evaluation Model

Each rule:

1. Targets one or more AudioCodes AVOM object types
2. Evaluates typed fields and evidence metadata from parsers
3. Uses topology relationships where cross-object checks are required
4. Returns a `HealthResult` with deterministic `PASS` or `FAIL` status
5. Assigns severity that affects the overall health score
6. Sets `recommendation=None` (no remediation guidance)

## Registration

AudioCodes rules register through `register_audiocodes_health_rules()` and load via `default_health_rule_registry()` alongside built-in, CUCM, and Teams rules.

```python
from health.health_engine import default_health_rule_registry

registry = default_health_rule_registry()
assert registry.get("audiocodes_sip_options_failed") is not None
```

## Scoring

Active failures and warnings reduce the base score of 100 using severity penalties:

| Severity | Penalty |
|----------|---------|
| Critical | 30 |
| High | 15 |
| Medium | 10 |
| Low | 5 |

## Module Layout

```text
core/health/audiocodes_rules.py    # 25 AudioCodes health rules
core/health/builtin_rules.py       # registers AudioCodes rules at bootstrap
```

## Related Tests

- [`../../tests/test_audiocodes_health_rules.py`](../../tests/test_audiocodes_health_rules.py)
- [`../../tests/test_health_engine.py`](../../tests/test_health_engine.py)

## Related Documentation

- [`audiocodes-parser-framework-v1.md`](audiocodes-parser-framework-v1.md)
- [`../../architecture/part-4-platform/14-audiocodes-health-engine.md`](../../architecture/part-4-platform/14-audiocodes-health-engine.md)
