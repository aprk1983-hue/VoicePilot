# Microsoft Teams Health Rules v1

## Purpose

Sprint 12.3 introduces deterministic Microsoft Teams health rules that evaluate CVOM objects produced by the Sprint 12.2 parser framework.

Rules are read-only: no Graph API, PowerShell execution, Microsoft authentication, recommendations, hypotheses, or remediation.

## Architecture

```text
Teams CVOM Objects + VoiceTopology
        │
        ▼
HealthEngine (Teams HealthRules)
        │
        ▼
HealthReport (HealthResult findings + score)
```

## Rule Categories

| Category | Rules |
|----------|-------|
| Licensing | Teams Phone license missing, Enterprise Voice disabled, Calling Plan license missing, Resource Account license missing |
| User Configuration | Phone number not assigned, Voice Routing Policy missing, Tenant Dial Plan missing, Caller ID policy missing, Location policy missing |
| Voice Routing | PSTN Usage missing, Voice Route missing, Voice Route without gateway, Gateway not referenced |
| Direct Routing | SBC unreachable, TLS certificate expired, SIP OPTIONS failed, Media Bypass disabled |
| Operator Connect | Operator Connect provider missing, Operator Connect number unassigned |
| Emergency Calling | Emergency Calling Policy missing, Emergency Routing Policy missing, LIS Location missing, Trusted IP missing |
| Resource Accounts | Auto Attendant missing Resource Account, Call Queue missing Resource Account, Resource Account unlicensed |

## Evaluation Model

Each rule:

1. Targets one or more Teams CVOM object types
2. Evaluates typed fields and evidence metadata from parsers
3. Uses topology relationships where cross-object checks are required
4. Returns a `HealthResult` with deterministic `PASS` or `FAIL` status
5. Assigns severity that affects the overall health score
6. Sets `recommendation=None` (no remediation guidance)

## Registration

Teams rules register through `register_teams_health_rules()` and are loaded by `default_health_rule_registry()` alongside built-in and CUCM rules.

```python
from health.health_engine import default_health_rule_registry

registry = default_health_rule_registry()
assert registry.get("teams_phone_license_missing") is not None
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
core/health/teams_rules.py    # 26 Teams health rules
core/health/builtin_rules.py  # registers Teams rules at bootstrap
```

## Related Tests

- [`../../tests/test_teams_health_rules.py`](../../tests/test_teams_health_rules.py)
- [`../../tests/test_health_engine.py`](../../tests/test_health_engine.py)

## Related Documentation

- [`teams-parser-framework-v1.md`](teams-parser-framework-v1.md)
- [`../../architecture/part-4-platform/10-microsoft-teams-health-engine.md`](../../architecture/part-4-platform/10-microsoft-teams-health-engine.md)
