# Verification Engine v1

Sprint 1 deliverable: engineer-controlled verification of likely root cause recommendations before learning capture.

## Scope

When a case reaches `RESOLUTION` with a `likely_root_cause` recommendation, VoicePilot generates a verification checklist from `recommendation.verification_steps`. The engineer marks each step `passed`, `failed`, or `not_tested` with optional notes.

**In v1:**

- Checklist only for `likely_root_cause` recommendations in `RESOLUTION`
- No verification for `next_best_action` cases still in `INVESTIGATION`
- Engineer-submitted results stored on `case.verifications`
- Deterministic state transitions based on results

**Not in v1:**

- AI validation of outcomes
- HTTP API or React UI
- Automated test call execution

## Behavior

| Case state | Recommendation type | Verification |
|------------|---------------------|--------------|
| `RESOLUTION` | `likely_root_cause` | Checklist generated |
| `INVESTIGATION` | `next_best_action` | Skipped |

### Result handling

| Outcome | Transition |
|---------|------------|
| All required steps `passed` | `RESOLUTION` → `VERIFICATION` → `LEARNING` |
| Any required step `failed` | `RESOLUTION` → `VERIFICATION` → `RESOLUTION` → `INVESTIGATION` |
| Incomplete / `not_tested` | Remains in `VERIFICATION` |

Failed verification adds a case note: root cause is not verified.

## Flow

```
Likely root cause recommendation (RESOLUTION)
        │
        ▼
generate_verification_checklist(case_id)
  → Verification records on case
        │
        ▼
Engineer marks each step
        │
        ▼
submit_verification(case_id, submissions)
        │
        ├── all passed → LEARNING
        └── any failed → INVESTIGATION
```

## API

```python
checklist = runtime.generate_verification_checklist(case_id)
summary = runtime.submit_verification(
    case_id,
    [VerificationResultSubmission(verification_id="...", status="passed", notes="")],
)
```

## CLI Output

```
Verification Checklist:
Likely root cause: CUBE SIP user agent disabled

[1] show sip-ua status reports SIP-UA enabled (required)
[2] Provider trunk shows registered/UP (required)
[3] Place controlled outbound test call (required)

Mark each step: passed / failed / not_tested
```

On success:

```
Verification complete. Next phase: LEARNING.
```

On failure:

```
Verification failed. Returning to INVESTIGATION.
```

## Tests

- `tests/test_verification_engine.py` — checklist, transitions, persistence
- `tests/test_cli.py` — checklist display and LEARNING transition

```bash
pytest tests/test_verification_engine.py tests/test_cli.py -v
```

## Next Steps

- Learning record capture in `LEARNING` phase
- Optional verification steps and waiver workflow
- Link verification outcomes to confidence score updates
