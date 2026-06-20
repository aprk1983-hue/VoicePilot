# Discovery Planner Framework

Deterministic, rule-based evidence planning for VoicePilot investigations.

## Purpose

Recommend the next CLI evidence to collect based on current case state — no AI, no persistence, no runtime integration in v1.

## Layout

| Module | Responsibility |
|--------|----------------|
| `planner_models.py` | `DiscoveryPriority`, `DiscoveryRequest`, `DiscoveryPlan`, scoring |
| `planner_rule.py` | `DiscoveryPlannerRule` contract |
| `planner_registry.py` | Rule registration and `evaluate(case)` |
| `planner_rules.py` | Built-in v1 rules |
| `planner_engine.py` | `PlannerEngine.evaluate_case()` |
| `planner_report.py` | Markdown formatter |
| `planner_bootstrap.py` | Default registry bootstrap |

## Usage

```python
from discovery import PlannerEngine

engine = PlannerEngine()
plan = engine.evaluate_case(case)
markdown = format_discovery_plan_markdown(plan)
```

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

## Related

- [Discovery framework v1 spec](../../docs/sprint-9/discovery-framework-v1.md)
