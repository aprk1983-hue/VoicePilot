# Discovery Planner Framework v1

Sprint 9.1 introduces a deterministic discovery planning framework that recommends the next evidence to collect based on the current investigation state.

## Goals

- Recommend ranked CLI evidence collection actions from case state
- Use explicit planner rules through a registry
- Produce immutable `DiscoveryPlan` and Markdown reports
- No AI, LLM, API, React, or persistence

## Architecture

```
Case (evidence, hypotheses, findings)
      ↓
DiscoveryPlannerRegistry.evaluate(case)
      ↓
PlannerEngine.evaluate_case(case)
      ↓
DiscoveryPlan + Markdown report
```

## Core models

### DiscoveryPriority

`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

### DiscoveryRequest

| Field | Purpose |
|-------|---------|
| `request_id` | Stable request identifier |
| `command` | CLI command to collect |
| `vendor` | Target vendor context |
| `priority` | Collection urgency |
| `reason` | Why the evidence is needed |
| `estimated_confidence_gain` | Expected confidence improvement |
| `estimated_minutes` | Estimated collection time |
| `related_hypotheses` | Hypothesis titles this evidence supports |
| `already_collected` | Whether evidence is already on the case |
| `optional` | Whether the request is supplemental |
| `score` | Deterministic ranking score |

### DiscoveryPlan

| Field | Purpose |
|-------|---------|
| `requests` | Ranked discovery requests |
| `current_confidence` | Top active hypothesis confidence |
| `estimated_final_confidence` | Projected confidence after all requests |
| `remaining_uncertainty` | `100 - current_confidence` |
| `next_best_command` | Highest-ranked pending command |
| `total_estimated_minutes` | Sum of estimated collection time |

## Scoring

```
score = priority_weight + estimated_confidence_gain + len(related_hypotheses)
```

| Priority | Weight |
|----------|--------|
| CRITICAL | 100 |
| HIGH | 75 |
| MEDIUM | 50 |
| LOW | 25 |

The engine deduplicates by `command`, keeps the highest score, excludes `already_collected` requests, and sorts descending by score.

## Built-in rules (v1)

| Rule ID | Command | Priority |
|---------|---------|----------|
| `dial_peer_summary_missing` | `show dial-peer voice summary` | CRITICAL |
| `sip_ua_status_missing` | `show sip-ua status` | HIGH |
| `voice_service_voip_missing` | `show run \| sec voice service voip` | HIGH |
| `ccsip_debug_missing` | `debug ccsip messages` | MEDIUM |
| `supplemental_dial_peer_config` | `show run \| sec dial-peer` | MEDIUM (optional) |

## Usage

```python
from discovery import PlannerEngine, format_discovery_plan_markdown

engine = PlannerEngine()
plan = engine.evaluate_case(case)
print(format_discovery_plan_markdown(plan))
```

## Current limitations

- No CLI or runtime integration in v1
- Built-in rules target Cisco CUBE outbound-failure evidence patterns
- Confidence projection is additive and capped at 100%
- Optional supplemental rules only fire when related routing hypotheses exist

## Tests

```bash
pytest tests/test_discovery_framework.py
```
