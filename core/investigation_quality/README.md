# Investigation Quality Framework

Deterministic, vendor-neutral evaluation of investigation quality.

## Purpose

Score whether an investigation has collected sufficient evidence and is ready to proceed toward recommendation or case closure — no AI, no persistence in v1.

## Layout

| Module | Responsibility |
|--------|----------------|
| `quality_models.py` | `QualityMetricResult`, `InvestigationQualityReport` |
| `quality_metric.py` | `InvestigationQualityMetric` contract |
| `quality_registry.py` | Metric registration and `evaluate(case)` |
| `builtin_metrics.py` | Built-in v1 metrics |
| `quality_engine.py` | `InvestigationQualityEngine.evaluate_case()` |
| `quality_report.py` | Markdown formatters |
| `quality_bootstrap.py` | Default registry bootstrap |

## Usage

```python
from investigation_quality import InvestigationQualityEngine, format_investigation_quality_markdown

report = InvestigationQualityEngine().evaluate_case(case)
print(format_investigation_quality_markdown(report))
```

## Built-in metrics (v1)

| Metric | Description |
|--------|-------------|
| `evidence_completeness` | Scores missing critical/optional evidence using `DiscoveryPlan` |

### Evidence completeness scoring

| Score | Condition |
|-------|-----------|
| 100 | All discovery evidence collected |
| 75 | One critical item missing |
| 50 | Multiple critical items missing |
| 0 | No evidence collected |

Critical priorities: `CRITICAL` and `HIGH` (non-optional requests).

## Related

- [Investigation quality framework v1 spec](../../docs/sprint-9/investigation-quality-framework-v1.md)
- [Discovery planner](../discovery/README.md)
