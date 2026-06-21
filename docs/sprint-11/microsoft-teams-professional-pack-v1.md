# Microsoft Teams Professional Knowledge Pack v1

## Purpose

Sprint 11.6 delivers production-quality Microsoft Teams Phone engineering assets built through the Engineering Asset Factory (EAF²). All assets pass factory validation and achieve quality scores of **95 or higher**.

This sprint creates deterministic engineering knowledge only. It does not include an investigation engine, Microsoft Graph, PowerShell, or live tenant connectivity.

## Architecture

```text
Vendor Asset SDK
        │
        ▼
Engineering Asset Factory
        │
        ▼
Microsoft Teams Assets
        │
        ▼
Engineering Knowledge Framework
        │
        ▼
Future Teams Investigation Engine
```

## Asset Inventory

| Type | Count | ID Range |
|------|-------|----------|
| Incidents | 25 | `VP-MS-TEAMS-000001` – `VP-MS-TEAMS-000025` |
| Runbooks | 10 | `VP-MS-TEAMS-RB-001` – `VP-MS-TEAMS-RB-010` |
| Verification Guides | 10 | `VP-MS-TEAMS-VG-001` – `VP-MS-TEAMS-VG-010` |
| References | 5 | `VP-MS-TEAMS-REF-001` – `VP-MS-TEAMS-REF-005` |
| **Total** | **50** | |

## Incident Categories

| Category | Incidents |
|----------|-----------|
| Licensing | 000001, 000002, 000016, 000024 |
| Operator Connect | 000006, 000023 |
| Direct Routing | 000007, 000022 |
| Calling Plans | 000016, 000024 |
| Voice Routing Policy | 000003 |
| Dial Plan | 000004 |
| Normalization Rules | 000005 |
| Emergency Calling | 000014 |
| Resource Accounts | 000013 |
| Auto Attendants | 000011 |
| Call Queues | 000012 |
| Teams Rooms | 000017 |
| Media Bypass | 000010 |
| TLS Certificate | 000008 |
| SBC Connectivity | 000018 |
| SIP OPTIONS | 000009, 000025 |
| Number Assignment | 000015 |
| Caller ID | 000019 |
| Location Policy | 000020 |
| Voice Routing Failure | 000021 |

## Example Incidents

- Teams Phone license missing (`VP-MS-TEAMS-000001`)
- Enterprise Voice disabled (`VP-MS-TEAMS-000002`)
- Voice Routing Policy missing (`VP-MS-TEAMS-000003`)
- Direct Routing SBC unreachable (`VP-MS-TEAMS-000007`)
- TLS certificate expired (`VP-MS-TEAMS-000008`)
- SIP OPTIONS failure (`VP-MS-TEAMS-000009`)
- Emergency Calling policy missing (`VP-MS-TEAMS-000014`)

## Runbooks

| ID | Name |
|----|------|
| RB-001 | Validate Enterprise Voice |
| RB-002 | Validate Voice Routing |
| RB-003 | Validate Direct Routing |
| RB-004 | Validate Operator Connect |
| RB-005 | Validate SBC Connectivity |
| RB-006 | Validate Licensing |
| RB-007 | Validate Emergency Calling |
| RB-008 | Validate Dial Plan |
| RB-009 | Validate Resource Accounts |
| RB-010 | Validate Auto Attendants |

## Verification Guides

| ID | Name |
|----|------|
| VG-001 | Verify Teams Phone license |
| VG-002 | Verify voice routing |
| VG-003 | Verify SBC connectivity |
| VG-004 | Verify TLS certificate |
| VG-005 | Verify emergency calling |
| VG-006 | Verify Direct Routing |
| VG-007 | Verify Operator Connect |
| VG-008 | Verify normalization rules |
| VG-009 | Verify caller ID |
| VG-010 | Verify Teams client |

## References

| ID | Title |
|----|-------|
| REF-001 | Microsoft Teams Voice Architecture |
| REF-002 | Direct Routing Reference |
| REF-003 | Operator Connect Guide |
| REF-004 | Teams Phone Licensing |
| REF-005 | Emergency Calling Reference |

## Relationships

Each incident links to:

- One or more runbooks (`VP-MS-TEAMS-RB-*`)
- One or more verification guides (`VP-MS-TEAMS-VG-*`)
- One or more references (`VP-MS-TEAMS-REF-*`)

Reference assets embed Microsoft Teams best-practice guidance for quality scoring and future investigation workflows.

## Quality Statistics

All 50 Microsoft Teams professional pack assets:

- Pass `EngineeringAssetFactory.validate_assets()`
- Score **≥ 95/100** on deterministic quality criteria
- Include required incident metadata: symptoms, findings, causes, resolution, rollback, verification

Validate locally:

```bash
voicepilot assets validate
voicepilot assets quality
voicepilot assets stats
voicepilot assets search Teams
voicepilot assets search "Direct Routing"
voicepilot assets show VP-MS-TEAMS-000001
```

## Location

```text
knowledge/incidents/microsoft/teams-phone/
knowledge/runbooks/microsoft/teams-phone/
knowledge/verification/microsoft/teams-phone/
knowledge/references/microsoft/teams-phone/
```

## Related Tests

- [`../../tests/test_microsoft_teams_knowledge_library.py`](../../tests/test_microsoft_teams_knowledge_library.py)

## Related Documentation

- [`engineering-asset-factory-v1.md`](engineering-asset-factory-v1.md)
- [`vendor-asset-sdk-v1.md`](vendor-asset-sdk-v1.md)
- [`../../architecture/part-4-platform/07-microsoft-teams-knowledge-library.md`](../../architecture/part-4-platform/07-microsoft-teams-knowledge-library.md)
