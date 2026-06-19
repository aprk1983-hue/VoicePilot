# Recommendation Engine v1

Sprint 1 deliverable: evidence-first recommendations from the top ranked hypothesis after `INVESTIGATION` begins.

## Scope

VoicePilot reads `case.hypotheses`, selects the top-ranked hypothesis, and produces either a **likely root cause** recommendation (high confidence) or a **next best action** recommendation (more evidence required).

**In v1:**

- Deterministic VP-CUBE-0001 action mappings
- Confidence threshold: **85%** (`DEFAULT_CONFIDENCE_THRESHOLD`)
- `RuntimeEngine.generate_recommendation(case_id)`
- CLI prints recommendation after hypotheses

**Not in v1:**

- AI reasoning
- Auto-applied configuration changes
- HTTP API or React UI
- Engineer approval workflow execution

## Behavior

| Top hypothesis confidence | Recommendation type | Case state after |
|---------------------------|---------------------|------------------|
| `>= 85%` | `likely_root_cause` | `RESOLUTION` |
| `< 85%` | `next_best_action` | `INVESTIGATION` |

High-confidence recommendations include:

- `likely_root_cause`
- `confidence`
- supporting `evidence` signals
- `recommended_actions`
- `verification_steps`
- `rollback_guidance` when configuration change is involved

Low-confidence recommendations explain that more evidence is needed and recommend the next command/action for the top hypothesis.

## VP-CUBE-0001 Mappings

| Hypothesis | Recommended focus |
|------------|-------------------|
| CUBE SIP user agent disabled | Check/enable `voice service voip` / SIP-UA |
| SIP registration/trunk issue | Verify `show sip-ua status` and provider registration |
| Provider/SIP trunk service issue | Check ITSP status, OPTIONS, provider routing |
| Codec / SDP negotiation issue | Review voice-class codec vs provider requirement |
| Network timeout / firewall issue | Collect packet capture and firewall logs |
| Provider rejection / caller ID issue | Verify caller ID format and provisioning |
| Routing / dial-peer issue | `show run \| sec dial-peer`, verify `destination-pattern` |
| Missing/unmatched dial-peer | Dial-peer coverage review and correction |

## Flow

```
Hypotheses generated (INVESTIGATION)
        │
        ▼
RuntimeEngine.generate_recommendation(case_id)
        │
        ▼
RecommendationEngine.generate(case)
  → Recommendation on case.recommendations
        │
        ├── confidence >= 85 → RESOLUTION
        └── confidence < 85  → remain INVESTIGATION
```

## API

```python
summary = runtime.generate_recommendation(case_id)
print(format_recommendation_summary(summary))
```

Requires case state `INVESTIGATION`.

## CLI Output

High confidence:

```
Likely Root Cause:
  CUBE SIP user agent disabled
Confidence: 90%
Evidence:
  - sip_ua_disabled
Recommended actions:
  - Review voice service voip configuration on CUBE
Verification steps:
  - show sip-ua status reports SIP-UA enabled
Rollback guidance:
  - Restore previous voice service voip sip configuration from change record
```

Low confidence:

```
Recommended Next Action:
  More evidence is needed before confirming root cause. Top hypothesis: Provider or SIP trunk service issue (75%)
Recommended actions:
  - Check ITSP/service provider status and incident notices
Verification steps:
  - Provider trunk returns healthy SIP response to OPTIONS
```

## Tests

- `tests/test_recommendation_engine.py` — threshold behavior, mappings, verification steps
- `tests/test_cli.py` — end-to-end recommendation output

```bash
pytest tests/test_recommendation_engine.py tests/test_cli.py -v
```

## Next Steps

- Engineer approval gates before RESOLUTION actions
- Playbook DSL `next_best_action` rule integration
- Link recommendations to `InvestigationStep` execution
