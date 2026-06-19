# Analysis v1

Sprint 1 deliverable: deterministic lightweight analysis of pasted CLI evidence after collection completes.

## Scope

When a case reaches `ANALYSIS`, VoicePilot scans collected evidence with simple pattern matchers. Findings are attached to the case and the lifecycle advances to `HYPOTHESIS`.

**In v1:**

- Regex and substring pattern matching only
- Per-command analyzers for VP-CUBE-0001 evidence types
- `RuntimeEngine.analyze_case(case_id)`
- CLI prints findings after evidence collection

**Not in v1:**

- AI reasoning
- Full SIP parser or playbook rule engine
- HTTP API or React UI
- Hypothesis discrimination (next sprint)

## Detected Signals

### `show sip-ua status`

| Pattern | Signal |
|---------|--------|
| `SIP-UA Status: enabled` or `SIP User Agent Status: enabled` | `sip_ua_enabled` |
| `disabled` | `sip_ua_disabled` |
| `registrar` / `registered` | `sip_registration_present` |
| `unregistered` / `failed` | `sip_registration_issue` |

### `show dial-peer voice summary`

| Pattern | Signal |
|---------|--------|
| `dial-peer` / `peer tag` / `destination-pattern` | `dial_peer_config_present` |
| empty or very short output | `dial_peer_summary_missing_or_empty` |
| `down` / `out of service` | `dial_peer_down` |

### `debug ccsip messages`

| Pattern | Signal |
|---------|--------|
| `404 Not Found` | `sip_404_detected` |
| `403 Forbidden` | `sip_403_detected` |
| `408 Request Timeout` | `sip_408_detected` |
| `488 Not Acceptable Here` | `sip_488_detected` |
| `503 Service Unavailable` | `sip_503_detected` |
| `From:` + `To:` + `Call-ID:` | `sip_trace_present` |

## Flow

```
Evidence collection complete (ANALYSIS)
        │
        ▼
RuntimeEngine.analyze_case(case_id)
        │
        ▼
AnalysisEngine.analyze(case)
  → AnalysisFinding[] on case
        │
        ▼
ANALYSIS → HYPOTHESIS
        │
        ▼
CLI prints findings
```

## Domain Model

`AnalysisFinding`:

| Field | Description |
|-------|-------------|
| `finding_id` | `FIND-{uuid}` |
| `case_id` | Investigation case |
| `evidence_id` | Source evidence artifact |
| `command` | CLI command analyzed |
| `signal` | Deterministic signal name |
| `detected_at` | Timestamp |

Stored on `Case.analysis_findings`. Linked evidence records receive `parser_finding_ids`.

## API

```python
from runtime.analysis_engine import AnalysisEngine, format_analysis_summary
from runtime.runtime_engine import RuntimeEngine

summary = runtime.analyze_case(case_id)
print(format_analysis_summary(summary))
```

## CLI Output

```
Evidence collection complete. Next phase: ANALYSIS.
Analysis complete. Next phase: HYPOTHESIS.
Findings:
- dial_peer_config_present
- sip_registration_present
- sip_trace_present
- sip_404_detected
```

## Tests

- `tests/test_analysis_engine.py` — pattern detection, `analyze_case`, findings persistence
- `tests/test_cli.py` — end-to-end findings output

```bash
pytest tests/test_analysis_engine.py tests/test_cli.py -v
```

## Next Steps

- Full SIP parser and playbook `parsers.findings` integration
- Map `AnalysisFinding` signals to hypothesis candidates
- Confidence scoring from finding combinations
