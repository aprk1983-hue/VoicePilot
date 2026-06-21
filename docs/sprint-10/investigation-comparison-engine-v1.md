# Investigation Comparison Engine v1

## Purpose

Sprint 10.9 introduces the **Investigation Comparison Engine (ICE)** — a deterministic before/after comparison framework for VoicePilot investigations and snapshots.

ICE compares existing investigation outputs. It never diagnoses, recommends, or executes configuration changes.

## Architecture

```text
Before Case / Snapshot          After Case / Snapshot
        │                                │
        ▼                                ▼
snapshot_from_case()          snapshot_from_case()
        │                                │
        └────────────┬───────────────────┘
                     ▼
      InvestigationComparisonEngine.compare_*()
                     │
                     ▼
      InvestigationComparison (frozen)
                     │
                     ▼
      format_comparison_markdown()
```

Metrics are extracted from existing outputs only:

- Health report (`build_incident_report` / `HealthEngine`)
- Investigation quality report
- Engineering knowledge matches (EKF)
- Analysis finding signals
- Verification status

## Comparison Status Rules

| Status | Condition |
|--------|-----------|
| `IMPROVED` | Critical findings reduced and/or key metrics improved with no regressions |
| `UNCHANGED` | No metric or finding changes |
| `REGRESSED` | Critical findings increased or metrics worsened without offsetting improvements |
| `PARTIAL` | Mixed improvements and regressions |

## Runtime Integration

```python
comparison = runtime.compare_cases(before_case_id, after_case_id)
comparison = runtime.compare_snapshots(before_snapshot, after_snapshot)
```

## Service Integration

```python
from services import VoicePilotService

service = VoicePilotService()
result = service.compare_cases(before_case_id, after_case_id)
# result.comparison_id, result.status, result.summary, result.markdown
```

## CLI Usage

```bash
voicepilot compare CASE-A CASE-B
voicepilot compare CASE-A CASE-B --output comparison.md

voicepilot compare-scenarios VP-CUBE-0001 sip_ua_disabled sip_ua_fixed
voicepilot compare-scenarios VP-CUBE-0001 sip_ua_disabled --output comparison.md
```

### Scenario Pairs

| Before | After (default) |
|--------|-----------------|
| sip_ua_disabled | sip_ua_fixed |
| provider_503 | provider_restored |
| dial_peer_shutdown | dial_peer_enabled |
| codec_mismatch_488 | codec_fixed |
| missing_outbound_dial_peer | dial_peer_added |

## Future Dashboard Usage

- Trend operational validation across remediation windows
- Embed comparison summaries in Executive and CAB reports (ERE integration point)
- Multi-case batch comparison for regression testing pipelines
- Snapshot timeline diff overlays with health score trends

## Read-Only Limitations

- Compares point-in-time investigation artifacts only
- Does not re-run analysis or alter case state beyond loading existing data
- Configuration snapshot comparison uses health/knowledge outputs only
