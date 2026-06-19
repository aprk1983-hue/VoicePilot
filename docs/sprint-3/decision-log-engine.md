# Decision Log Engine v1

The Decision Log Engine is VoicePilot's append-only audit trail for investigation decisions. Every important step records what happened, why, which evidence and rules were involved, and how confidence changed.

## Architecture

```
Parser / Analysis / Correlation / Recommendation / Verification / Learning
                              ↓
                    DecisionLogEngine.append*()
                              ↓
                    Case.decision_log (immutable entries)
                              ↓
              CLI `voicepilot decisions` + Incident Report
```

The engine is vendor-neutral. Parser names, rule names, evidence IDs, finding IDs, and confidence values are stored as structured fields — not prose summaries alone.

## Append-only design

- Entries are **never edited or deleted**
- `DecisionLogEngine.append()` only adds to `case.decision_log`
- Duplicate entry IDs raise `DecisionLogImmutableError`
- `DecisionLogEntry` is a frozen dataclass

## Domain model

`DecisionLogEntry` fields:

| Field | Purpose |
|-------|---------|
| `entry_id` | Unique ID (`DLOG-…`) |
| `timestamp` | UTC time of the decision |
| `case_id` | Investigation case |
| `stage` | Investigation state when recorded |
| `decision_type` | See `DecisionLogEntryType` enum |
| `title` / `description` | Human-readable summary |
| `confidence_before` / `confidence_after` / `confidence_delta` | Confidence audit |
| `trigger` | Rule type or event trigger |
| `supporting_findings` | Finding IDs or signal names |
| `supporting_correlations` | Correlation IDs |
| `supporting_evidence` | Evidence IDs |
| `rejected_hypotheses` | Alternatives not selected |
| `selected_hypothesis` | Chosen hypothesis ID |
| `rule_name` | Parser ID or correlation rule |
| `engine` | Source engine name |
| `severity` | Case severity at time of entry |
| `user_visible` | Shown in engineer-facing output |
| `metadata` | Additional structured context |

## Decision types

`DecisionLogEntryType` values:

- `QUESTION_SELECTED`
- `EVIDENCE_COLLECTED`
- `PARSER_RESULT`
- `ANALYSIS_RESULT`
- `CORRELATION`
- `HYPOTHESIS_CREATED`
- `HYPOTHESIS_REJECTED`
- `CONFIDENCE_INCREASED`
- `CONFIDENCE_DECREASED`
- `RECOMMENDATION_SELECTED`
- `VERIFICATION_COMPLETED`
- `LEARNING_CREATED`
- `CASE_CLOSED`

## Runtime integration

`RuntimeEngine` owns a `DecisionLogEngine` and appends entries when:

| Event | Decision type |
|-------|----------------|
| Evidence submitted (CLI) | `EVIDENCE_COLLECTED` |
| Parser finding produced | `PARSER_RESULT` |
| V1 analysis finding | `ANALYSIS_RESULT` |
| Hypothesis generated | `HYPOTHESIS_CREATED` |
| Correlation fires | `CORRELATION` |
| Confidence adjusted | `CONFIDENCE_INCREASED` / `DECREASED` |
| Recommendation chosen | `RECOMMENDATION_SELECTED` |
| Verification recorded | `VERIFICATION_COMPLETED` |
| Learning record created | `LEARNING_CREATED` |
| Case closed | `CASE_CLOSED` |

## CLI

```bash
voicepilot decisions CASE-ID
```

Prints the complete chronological decision timeline.

## Incident report

Closed-case reports include a **Decision Timeline** section with the same chronological narrative used by the CLI.

## Enterprise compliance

- Full audit trail of automated and engineer-driven steps
- Confidence changes are explainable and tied to rules and evidence
- Immutable log supports regulatory and operational review
- Future SIEM integration can export `case.decision_log` as structured JSON events

## Tests

`tests/test_decision_log_engine.py` covers unit append methods, runtime integration, timeline ordering, and immutability guarantees.
