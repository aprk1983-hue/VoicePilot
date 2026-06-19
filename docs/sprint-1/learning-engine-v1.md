# Learning Engine v1

Sprint 1 deliverable: structured learning capture and case closure after successful verification.

## Scope

When a case reaches `LEARNING` after verification passes, VoicePilot creates a structured `LearningRecord` and transitions the case to `CLOSED`. No model training occurs — records are stored for future retrieval and analytics only.

**In v1:**

- Deterministic learning record from case artifacts
- `RuntimeEngine.close_case_with_learning(case_id)`
- CLI auto-closure after verification success
- Engineer remains in control; closure only after explicit verification pass

**Not in v1:**

- AI / LLM training
- Knowledge corpus indexing
- HTTP API or React UI
- SME review queue

## Learning Record Fields

| Field | Source |
|-------|--------|
| `learning_record_id` | `LRN-{uuid}` |
| `case_id` | Active case |
| `playbook_id` | Bound playbook |
| `symptom` | `case.symptom.summary` |
| `root_cause` | Top hypothesis / likely root cause recommendation |
| `confidence` | Recommendation or hypothesis confidence |
| `evidence_summary` | Analysis finding signals |
| `resolution_summary` | Recommended resolution actions |
| `verification_summary` | Passed verification steps |
| `lessons_learned` | Deterministic closure narrative |
| `reusable_pattern` | `{playbook_id}:{hypothesis_category}` |
| `final_outcome` | `verified_and_closed` |
| `evidence_finding_ids` | Linked analysis finding IDs |

## Flow

```
Verification complete (LEARNING)
        │
        ▼
close_case_with_learning(case_id)
        │
        ▼
LearningEngine.create_learning_record(case)
  → LearningRecord on case
        │
        ▼
LEARNING → CLOSED
        │
        ▼
CLI prints closure summary
```

## API

```python
summary = runtime.close_case_with_learning(case_id)
print(format_learning_closure_summary(summary))
```

Requires case state `LEARNING`.

## CLI Output

```
Verification complete. Next phase: LEARNING.
Case closed.
Learning record created.
Learning Record: LRN-abc123
Root cause: CUBE SIP user agent disabled
Confidence: 90%
```

## Tests

- `tests/test_learning_engine.py` — record creation, closure, state guard
- `tests/test_cli.py` — end-to-end closure output

```bash
pytest tests/test_learning_engine.py tests/test_cli.py -v
```

## Next Steps

- Knowledge Engine indexing of approved learning records
- Anonymization rules from playbook DSL `learning.anonymize`
- Organizational trend reports from closed-case learning corpus
