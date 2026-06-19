# Intake Summary v1

Sprint 1 deliverable: structured investigation summary when intake completes and the case enters `DISCOVERY`.

## Scope

After all `INTAKE`-phase questions are answered, VoicePilot builds a deterministic summary from intake answers and playbook-specific rules. No AI, no log parser, no evidence evaluation yet.

## Summary Fields

| Field | Description |
|-------|-------------|
| `case_id` | Active investigation case |
| `playbook_id` | Bound playbook ID |
| `current_state` | Lifecycle state after intake (typically `DISCOVERY`) |
| `known_facts` | Intake answers mapped from `target_field` values |
| `missing_evidence` | Evidence still required before confirmation |
| `recommended_strategy` | Deterministic strategy hint from intake signals |
| `next_required_commands` | CLI commands to collect first evidence |

## VP-CUBE-0001 Rules

### Strategy selection

When intake indicates outbound calling **worked previously** and a **recent change** was reported:

```
recommended_strategy = "Change-first / Routing-first"
```

Otherwise the default is:

```
recommended_strategy = "Routing-first"
```

Recent change negatives: `no`, `none`, `no changes`, `n/a`, `nothing`, `unknown`.

### Missing evidence

When intake indicates **all outbound calls are failing**:

```
missing_evidence:
  - show dial-peer voice summary
  - show sip-ua status
  - debug ccsip messages
```

`next_required_commands` mirrors `missing_evidence` for this playbook.

## Implementation

| Module | Role |
|--------|------|
| `core/runtime/intake_summary.py` | `IntakeSummary`, `build_intake_summary()`, `format_intake_summary()` |
| `cli/voicepilot_cli.py` | Prints summary after intake completes |

```python
from runtime.intake_summary import build_intake_summary, format_intake_summary

summary = build_intake_summary(case, playbook)
print(format_intake_summary(summary))
```

## CLI Output

```
Intake complete. Next phase: DISCOVERY.

--- Intake Summary ---
Case ID:     CASE-abc123
Playbook:    VP-CUBE-0001
State:       DISCOVERY

Known Facts:
  worked_previously: yes
  recent_changes: firewall change
  onset: 2026-06-10
  destination_classes: all destinations
  inbound_working: yes

Missing Evidence:
  - show dial-peer voice summary
  - show sip-ua status
  - debug ccsip messages

Recommended Strategy:
  Change-first / Routing-first

Next Required Commands:
  - show dial-peer voice summary
  - show sip-ua status
  - debug ccsip messages
```

## Tests

- `tests/test_intake_summary.py` — builder rules and formatting
- `tests/test_cli.py` — CLI prints summary after intake

```bash
pytest tests/test_intake_summary.py tests/test_cli.py -v
```

## Next Steps

- Load missing evidence and commands from playbook DSL `evidence` blocks
- Strategy selection from playbook `strategies` weights
- Evidence collection loop after summary
