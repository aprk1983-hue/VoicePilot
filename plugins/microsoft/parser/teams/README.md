# Microsoft Teams Parser Pack

Deterministic parsers for exported Microsoft Teams Phone PowerShell evidence.

## Cmdlets

- `Get-CsOnlineUser`
- `Get-CsPhoneNumberAssignment`
- `Get-CsOnlineVoiceRoutingPolicy`
- `Get-CsOnlineVoiceRoute`
- `Get-CsTenantDialPlan`
- `Get-CsOnlinePSTNGateway`
- `Get-CsOnlinePstnUsage`
- `Get-CsCallQueue`
- `Get-CsAutoAttendant`
- `Get-CsResourceAccount`
- `Get-CsOnlineLisLocation`

## Evidence Formats

CSV, JSON, and PowerShell Format-List exports under `examples/sample_evidence/teams/`.

## Registration

```python
from plugins.microsoft.parser.teams import register_teams_parsers
register_teams_parsers(registry)
```
