# Correlation Reporting v1

Incident reports now include a **Correlation Reasoning** section that explains how cross-finding correlations affected hypothesis confidence before the final recommendation.

## Goals

- Make confidence changes auditable in the closed-case report
- Surface reinforcement, contradiction, and signal correlations with evidence
- No AI, no API/React

## Report section

After **Evidence Findings** and before **Recommendation**, the report includes:

```markdown
## Correlation Reasoning

- **sip_ua_disabled_confirmed** — reinforcement, +8 confidence
  Operational status and running configuration both indicate SIP-UA is disabled.
  Evidence: sip_ua_disabled, sip_ua_disabled_by_config
```

Each entry includes:

| Field | Source |
|-------|--------|
| Correlation name | `CorrelationResult.rule_id` |
| Type | `reinforcement`, `contradiction`, or `signal` |
| Confidence impact | `confidence_delta` (omitted when zero) |
| Explanation | Human-readable rationale from the correlation rule |
| Evidence | `finding_codes` from the correlation |

When no correlations were produced, the section shows:

```markdown
_No correlation results recorded._
```

## Data model

`IncidentReport` includes `correlations: tuple[ReportCorrelation, ...]` built from `Case.correlation_results` at report generation time.

## Flow

Correlation runs during investigation (CLI/demo) before recommendation. The closed-case report reads persisted `case.correlation_results` — it does not re-run the correlation engine.

## Tests

- `tests/test_report_engine.py` — section content, SIP-UA confirmation example, empty correlations
- `tests/test_demo_runner.py` — demo report file includes correlation reasoning
