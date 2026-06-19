# Hypothesis Engine v1

Sprint 1 deliverable: deterministic ranked hypotheses from analysis findings after the case reaches `HYPOTHESIS`.

## Scope

VoicePilot reads `case.analysis_findings`, applies VP-CUBE-0001 rule mappings, creates ranked `Hypothesis` objects, and advances the case to `INVESTIGATION`.

**In v1:**

- Deterministic finding → hypothesis rules
- Ranked hypotheses with confidence percentages
- Supporting finding IDs linked on each hypothesis
- `RuntimeEngine.generate_hypotheses(case_id)`
- CLI prints hypotheses after analysis

**Not in v1:**

- AI reasoning
- Auto-confirmed root cause (all hypotheses remain `candidate`)
- HTTP API or React UI
- Playbook DSL rule engine integration

## VP-CUBE-0001 Rules

| Findings | Hypothesis | Confidence |
|----------|------------|------------|
| `sip_404_detected` + `dial_peer_config_present` | Routing / dial-peer issue | 70% |
| `sip_404_detected` without dial-peer evidence | Missing or unmatched outbound dial-peer | 82% |
| `sip_503_detected` + `sip_trace_present` | Provider or SIP trunk service issue | 75% |
| `sip_488_detected` | Codec / SDP negotiation issue | 78% |
| `sip_408_detected` | Network timeout / firewall / provider no response | 76% |
| `sip_403_detected` | Provider rejection / caller ID / authorization issue | 74% |
| `sip_ua_disabled` | CUBE SIP user agent disabled | 90% |
| `sip_registration_issue` | SIP registration/trunk availability issue | 86% |

When no findings are available, a single low-confidence fallback hypothesis is created:

- **Insufficient evidence to rank root cause** — 25%

## Flow

```
Analysis complete (HYPOTHESIS)
        │
        ▼
RuntimeEngine.generate_hypotheses(case_id)
        │
        ▼
HypothesisEngine.generate(case)
  → ranked Hypothesis[] on case
        │
        ▼
HYPOTHESIS → INVESTIGATION
        │
        ▼
CLI prints hypothesis summary
```

## Hypothesis Model

Extended fields used in v1:

| Field | Description |
|-------|-------------|
| `hypothesis_id` | `HYP-{uuid}` |
| `title` | Human-readable hypothesis title |
| `confidence` | Deterministic confidence score (0–100) |
| `supporting_finding_ids` | Linked `AnalysisFinding` IDs |
| `contradicting_finding_ids` | Reserved for future contradiction rules |
| `status` | Always `candidate` in v1 |
| `explanation` | Why the rule matched |
| `next_best_action` | Recommended next investigative step |

## API

```python
summary = runtime.generate_hypotheses(case_id)
print(format_hypothesis_summary(summary))
```

Requires case state `HYPOTHESIS`.

## CLI Output

```
Hypothesis generation complete. Next phase: INVESTIGATION.
Hypotheses:
- Provider or SIP trunk service issue — 75%
  Evidence: sip_503_detected, sip_trace_present
  Next action: Verify provider status and SIP trunk health.
```

## Tests

- `tests/test_hypothesis_engine.py` — rule matching, state transition, persistence
- `tests/test_cli.py` — end-to-end hypothesis output

```bash
pytest tests/test_hypothesis_engine.py tests/test_cli.py -v
```

## Next Steps

- Hypothesis discrimination and elimination
- Confidence gates before `confirmed` status
- Playbook DSL `hypotheses` and `rules.evidence` integration
