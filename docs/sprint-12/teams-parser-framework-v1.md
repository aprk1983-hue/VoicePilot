# Microsoft Teams Parser Framework v1

## Purpose

Sprint 12.2 introduces deterministic Microsoft Teams parsers that convert exported PowerShell evidence into CVOM (Canonical Voice Object Model) objects.

The framework is read-only: no Graph API, no PowerShell execution, and no Microsoft authentication.

## Architecture

```text
Exported PowerShell Evidence (CSV / JSON / Format-List)
        │
        ▼
TeamsPowerShellParser (detect → parse → validate)
        │
        ▼
ParserResult (structured_data, findings, voice_objects)
        │
        ▼
TopologyBuilder + RelationshipBuilder
        │
        ▼
VoiceTopology (Teams CVOM buckets + relationships)
```

## Package Layout

```text
plugins/microsoft/parser/teams/
  _evidence.py          # CSV / JSON / Format-List parsing
  _base.py              # TeamsPowerShellParser base class
  _helpers.py           # Shared metadata helpers
  get_csonlineuser.py
  get_csphonenumberassignment.py
  get_csonlinevoiceroutingpolicy.py
  get_csonlinevoiceroute.py
  get_cstenantdialplan.py
  get_csonlinepstngateway.py
  get_csonlinepstnusage.py
  get_cscallqueue.py
  get_csautoattendant.py
  get_csresourceaccount.py
  get_csonlinelislocation.py
```

## Supported Cmdlets

| Cmdlet | CVOM Type | Parser ID |
|--------|-----------|-----------|
| Get-CsOnlineUser | `teams_user` | `microsoft_get_csonlineuser` |
| Get-CsPhoneNumberAssignment | `teams_phone_number` | `microsoft_get_csphonenumberassignment` |
| Get-CsOnlineVoiceRoutingPolicy | `teams_voice_routing_policy` | `microsoft_get_csonlinevoiceroutingpolicy` |
| Get-CsOnlineVoiceRoute | `teams_voice_route` | `microsoft_get_csonlinevoiceroute` |
| Get-CsTenantDialPlan | `teams_dial_plan` | `microsoft_get_cstenantdialplan` |
| Get-CsOnlinePSTNGateway | `teams_pstn_gateway` | `microsoft_get_csonlinepstngateway` |
| Get-CsOnlinePstnUsage | `teams_pstn_usage` | `microsoft_get_csonlinepstnusage` |
| Get-CsCallQueue | `teams_call_queue` | `microsoft_get_cscallqueue` |
| Get-CsAutoAttendant | `teams_auto_attendant` | `microsoft_get_csautoattendant` |
| Get-CsResourceAccount | `teams_resource_account` | `microsoft_get_csresourceaccount` |
| Get-CsOnlineLisLocation | `teams_lis_location` | `microsoft_get_csonlinelislocation` |

## Evidence Formats

Parsers accept:

- **Format-List** — `PropertyName : Value` PowerShell output
- **CSV** — exported cmdlet results
- **JSON** — `ConvertTo-Json` output

Unknown fields are preserved in record metadata and ignored for schema validation.

## Parser Behavior

Each parser:

1. Detects supported evidence via cmdlet markers and property names
2. Validates required schema fields per cmdlet
3. Deduplicates records by identity (last wins, warning logged)
4. Emits immutable CVOM objects with provenance (`source_parser`, `source_command`, `source_evidence_id`)
5. Produces investigation findings aligned with Teams knowledge pack signals

## Registration

```python
from parser.parser_registry import ParserRegistry
from plugins.microsoft.parser import register_microsoft_parsers

registry = ParserRegistry()
register_microsoft_parsers(registry)
```

`build_default_parser_engine()` registers both Cisco and Microsoft parsers.

## Topology Integration

`TopologyBuilder` partitions Teams CVOM objects into dedicated buckets on `VoiceTopology`.

`RelationshipBuilder` infers:

- Teams user → voice routing policy (`uses`)
- Voice route → PSTN usage (`uses`)
- Voice route → PSTN gateway (`routes_to`)
- Call queue / auto attendant → resource account (`uses`)

## Sample Evidence

```text
examples/sample_evidence/teams/
  get_csonlineuser_format_list.txt
  get_csonlineuser.csv
  get_csonlineuser.json
  ...
```

## Related Tests

- [`../../tests/test_teams_parser_framework.py`](../../tests/test_teams_parser_framework.py)

## Related Documentation

- [`../../docs/parser-framework.md`](../../docs/parser-framework.md)
- [`../../architecture/part-4-platform/09-microsoft-teams-parser-pipeline.md`](../../architecture/part-4-platform/09-microsoft-teams-parser-pipeline.md)
- [`microsoft-teams-professional-pack-v1.md`](microsoft-teams-professional-pack-v1.md)
