# Correlation Engine v1

VoicePilot's correlation engine combines independent parser and analysis findings to reinforce or contradict hypotheses before recommendations are generated.

## Goals

- Increase confidence when independent evidence agrees
- Surface contradictions that require more evidence
- Remain vendor-neutral at the engine layer (rules target VP-CUBE-0001 initially)
- No AI, no API/React

## Flow

```
ANALYSIS → HYPOTHESIS → INVESTIGATION
                ↓
         correlate_case()
                ↓
    update hypothesis confidence
                ↓
      generate_recommendation()
```

The CLI runs correlation after hypothesis generation and before recommendation. Correlation does not auto-close cases.

## Domain model

`CorrelationResult` is stored on `Case.correlation_results`:

| Field | Description |
|-------|-------------|
| `correlation_id` | Unique ID (`COR-…`) |
| `correlation_type` | `reinforcement`, `contradiction`, or `signal` |
| `rule_id` | Stable rule identifier |
| `explanation` | Human-readable rationale |
| `finding_codes` | Signals that triggered the rule |
| `confidence_delta` | Applied change to hypothesis confidence |
| `hypothesis_id` | Target hypothesis when confidence changed |

## Rules (VP-CUBE-0001 v1)

### A. SIP-UA Disabled Confirmation

**IF** `sip_ua_disabled` **AND** `sip_ua_disabled_by_config`

- Correlation: `sip_ua_disabled_confirmed`
- Boost **CUBE SIP user agent disabled** by +8 (max 98%)
- Explanation: Operational status and running configuration both indicate SIP-UA is disabled.

### B. SIP-UA Status Contradiction

**IF** `sip_ua_enabled` **AND** `sip_ua_disabled_by_config`

- Contradiction: `sip_ua_status_config_mismatch`
- Reduce **CUBE SIP user agent disabled** by −10
- Explanation: Operational status says enabled, but config suggests disabled.

### C. Provider / Trunk Signal

**IF** `sip_503_detected` **AND** `sip_registration_issue`

- Correlation: `provider_or_trunk_unavailable`
- Boost **Provider or SIP trunk service issue** by +10

### D. Routing Signal

**IF** `sip_404_detected` **AND** `dial_peer_summary_missing_or_empty`

- Correlation: `routing_evidence_missing_dial_peer`
- Boost **Missing or unmatched outbound dial-peer** by +10

### E. Codec Signal

**IF** `sip_488_detected`

- Correlation: `codec_negotiation_failure_signal`
- No confidence boost (SDP details required to confirm)

## Runtime API

```python
summary = runtime.correlate_case(case_id)
```

Requires `INVESTIGATION` or `HYPOTHESIS` with hypotheses present. Persists `case.correlation_results` and updated hypothesis confidence.

## CLI output

```
Correlation complete.
Correlations:
- sip_ua_disabled_confirmed (+8 confidence)
```

## Demo evidence

VP-CUBE-0001 demo includes `show run | sec voice service voip` so SIP-UA disabled can be confirmed by both operational status and configuration.

## Tests

- `tests/test_correlation_engine.py` — rule behavior and runtime guard
- `tests/test_cli.py` — correlation printed in full investigation flow
- `tests/test_demo_runner.py` — report shows 98% confidence when both SIP-UA signals are present
