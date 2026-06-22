# Microsoft Teams Investigation Engine v1

## Purpose

Sprint 12.4 introduces a deterministic Microsoft Teams Phone investigation engine integrated with the VoicePilot runtime pipeline.

The engine is read-only: no Graph API, PowerShell execution, Microsoft authentication, or configuration changes.

## Playbook

**ID:** `VP-TEAMS-0001`

**Path:** `plugins/microsoft/playbooks/teams/vp-teams-0001-microsoft-teams-investigation.vpb.yaml`

## Investigation Pipeline

```text
Intake → Evidence Collection → Parser Analysis → Hypotheses → Correlation
  → Discovery Planner → Investigation Quality → Recommendations
  → Engineering Change Package → Enterprise Reports
```

## Hypotheses

Eleven deterministic hypotheses:

- Teams Phone license missing
- Enterprise Voice disabled
- Phone number not assigned
- Voice Routing Policy missing
- PSTN Usage missing
- Voice Route missing
- Direct Routing SBC unreachable
- TLS certificate expired
- SIP OPTIONS failed
- Emergency Calling configuration issue
- Resource Account issue

## Engine Modules

| Module | Path |
|--------|------|
| Investigation rules | `core/runtime/teams_investigation.py` |
| Intake summary | `core/runtime/intake_summary.py` |
| Discovery planner | `core/discovery/teams_planner_rules.py` |
| Health rules | `core/health/teams_rules.py` |
| Parsers | `plugins/microsoft/parser/teams/` |
| Scenario pack | `examples/sample_evidence/scenarios/vp_teams_0001/` |

## CLI Commands

```bash
voicepilot investigate VP-TEAMS-0001
voicepilot scenarios VP-TEAMS-0001
voicepilot scenarios VP-TEAMS-0001 --scenario teams_phone_license_missing
voicepilot report-scenario VP-TEAMS-0001 --scenario direct_routing_sbc_unreachable --type executive
voicepilot change-package-scenario VP-TEAMS-0001 --scenario tls_certificate_expired
voicepilot plan-scenario VP-TEAMS-0001 --scenario pstn_usage_missing
voicepilot quality-scenario VP-TEAMS-0001 --scenario pstn_usage_missing
voicepilot validate VP-TEAMS-0001
```

## Scenario Pack

Eleven scenarios under `examples/sample_evidence/scenarios/vp_teams_0001/`:

- `teams_phone_license_missing`
- `enterprise_voice_disabled`
- `phone_number_not_assigned`
- `voice_routing_policy_missing`
- `pstn_usage_missing`
- `voice_route_missing`
- `direct_routing_sbc_unreachable`
- `tls_certificate_expired`
- `sip_options_failed`
- `emergency_calling_configuration`
- `resource_account_issue`

## Related Tests

- [`../../tests/test_teams_investigation_engine.py`](../../tests/test_teams_investigation_engine.py)
- [`../../tests/test_vp_teams_0001_scenarios.py`](../../tests/test_vp_teams_0001_scenarios.py)

## Related Documentation

- [`teams-parser-framework-v1.md`](teams-parser-framework-v1.md)
- [`teams-health-rules-v1.md`](teams-health-rules-v1.md)
- [`../../architecture/part-4-platform/11-microsoft-teams-investigation-engine.md`](../../architecture/part-4-platform/11-microsoft-teams-investigation-engine.md)
