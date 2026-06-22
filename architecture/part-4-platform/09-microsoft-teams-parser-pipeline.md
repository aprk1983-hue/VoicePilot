# 09 — Microsoft Teams Parser Pipeline

> **Status:** Implemented

## Purpose

Document the Microsoft Teams Parser Framework: deterministic parsers that convert exported PowerShell evidence into CVOM objects for Teams Phone investigations.

No Graph API, PowerShell execution, or live tenant connectivity is involved.

## Repository Modules Involved

- [`../../plugins/microsoft/parser/teams/`](../../plugins/microsoft/parser/teams/) — Teams PowerShell parsers
- [`../../core/model/teams_objects.py`](../../core/model/teams_objects.py) — Teams CVOM types
- [`../../core/parser/`](../../core/parser/) — parser framework interfaces
- [`../../core/runtime/parser_bootstrap.py`](../../core/runtime/parser_bootstrap.py) — parser engine bootstrap
- [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py) — topology assembly
- [`../../core/topology/relationship_builder.py`](../../core/topology/relationship_builder.py) — Teams relationship rules

## Pipeline

```text
PowerShell Evidence → Teams Parser → CVOM VoiceObjects → TopologyBuilder → VoiceTopology
```

## Supported Cmdlets

Eleven Teams Phone cmdlets are supported:

- Get-CsOnlineUser
- Get-CsPhoneNumberAssignment
- Get-CsOnlineVoiceRoutingPolicy
- Get-CsOnlineVoiceRoute
- Get-CsTenantDialPlan
- Get-CsOnlinePSTNGateway
- Get-CsOnlinePstnUsage
- Get-CsCallQueue
- Get-CsAutoAttendant
- Get-CsResourceAccount
- Get-CsOnlineLisLocation

## Evidence Formats

CSV, JSON, and PowerShell Format-List text exports.

## CVOM Types

Teams-specific immutable objects in `core/model/teams_objects.py` with object types prefixed `teams_*`.

## Topology Relationships

| Source | Relationship | Target |
|--------|--------------|--------|
| Teams user | uses | Voice routing policy |
| Voice route | uses | PSTN usage |
| Voice route | routes_to | PSTN gateway |
| Call queue | uses | Resource account |
| Auto attendant | uses | Resource account |

## Related Tests

- [`../../tests/test_teams_parser_framework.py`](../../tests/test_teams_parser_framework.py)

## Related Documentation

- [`../../docs/sprint-12/teams-parser-framework-v1.md`](../../docs/sprint-12/teams-parser-framework-v1.md)
- [07 — Microsoft Teams Knowledge Library](07-microsoft-teams-knowledge-library.md)

## Cross References

- [02 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [03 — Topology Engines](../part-3-engines/03-topology-engines.md)
