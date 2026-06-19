# Evidence Collection v1

Sprint 1 deliverable: collect required CLI command outputs after intake summary via engineer paste.

## Scope

After intake completes and the case enters `DISCOVERY`, VoicePilot requests required command outputs derived from the intake summary. Engineers paste multi-line CLI output; collection advances command by command until the case moves to `ANALYSIS`.

**In v1:**

- Required commands from `IntakeSummary.next_required_commands`
- Multi-line paste terminated with `END` on its own line
- Evidence saved on the case with `source_type = cli_paste`
- State transitions: `DISCOVERY` → `COLLECTION` → `ANALYSIS`

**Not in v1:**

- AI reasoning or SIP parser
- HTTP API or React UI
- Automated device SSH collection
- Evidence quality scoring beyond placeholders

## Flow

```
Intake complete (DISCOVERY)
        │
        ▼
Intake summary printed
        │
        ▼
initialize_evidence_collection()
  DISCOVERY → COLLECTION
        │
        ▼
Please provide command output:
show dial-peer voice summary
(paste; type END to finish)
        │
        ▼
submit_evidence() → Evidence on case
        │
        ├── more commands → next request
        │
        └── all collected → ANALYSIS
              "Evidence collection complete. Next phase: ANALYSIS."
```

## Domain Models

| Model | Purpose |
|-------|---------|
| `EvidenceRequest` | Next command to collect (`command`, `sequence`, `total`) |
| `EvidenceSubmission` | Result of a paste submission |
| `Evidence` | Extended with `source_type`, `raw_text`; `create_cli_paste()` factory |

Saved evidence fields:

- `case_id`
- `source.command`
- `source_type = cli_paste`
- `raw_text`
- `collected_at`

## VP-CUBE-0001 Required Commands

When intake indicates all outbound calls are failing:

1. `show dial-peer voice summary`
2. `show sip-ua status`
3. `debug ccsip messages`

## CLI

```bash
voicepilot investigate VP-CUBE-0001
```

After intake summary:

```
Please provide command output:
show dial-peer voice summary
(paste output; type END on its own line to finish)
> dial-peer 1 voip up
> END
```

## Implementation

| Module | Role |
|--------|------|
| `core/runtime/evidence_collection.py` | Collection state, requests, submissions |
| `cli/voicepilot_cli.py` | `read_multiline_paste()`, `run_evidence_collection()` |

## Tests

- `tests/test_evidence_collection.py` — request order, evidence persistence, state transition
- `tests/test_cli.py` — `END` marker and full investigate flow

```bash
pytest tests/test_evidence_collection.py tests/test_cli.py -v
```

## Next Steps

- Load required commands from playbook DSL `evidence.commands`
- SIP parser integration on submitted `raw_text`
- Evidence validation and quality scoring
