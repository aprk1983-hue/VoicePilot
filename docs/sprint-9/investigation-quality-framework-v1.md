# Investigation Quality Framework v1

Sprint 9.3 adds a deterministic, vendor-neutral framework for scoring investigation quality. No AI, no LLM, no persistence in v1.

## Package layout

```
core/investigation_quality/
├── quality_models.py      # QualityMetricResult, InvestigationQualityReport
├── quality_metric.py      # InvestigationQualityMetric contract
├── quality_registry.py    # Metric registration and evaluate(case)
├── builtin_metrics.py     # EvidenceCompletenessMetric (v1)
├── quality_engine.py      # InvestigationQualityEngine.evaluate_case()
├── quality_report.py      # Markdown formatters
├── quality_bootstrap.py   # Default registry bootstrap
└── README.md
```

## Models

### QualityMetricResult

Frozen dataclass with:

- `metric_name`
- `score`
- `max_score`
- `status` (`PASS`, `WARN`, `FAIL`, `UNKNOWN`)
- `summary`
- `recommendations`

### InvestigationQualityReport

Frozen dataclass with:

- `overall_score`
- `overall_status`
- `metric_results`
- `ready_for_recommendation`
- `ready_for_case_closure`
- `generated_at`

## Metric interface

```python
class InvestigationQualityMetric(ABC):
    def evaluate(self, case: Case) -> QualityMetricResult:
        ...
```

## Registry

`InvestigationQualityRegistry`:

- `register_metric(metric)` — rejects duplicate metric names
- `evaluate(case)` — runs all metrics in deterministic name order

## Built-in metric: evidence completeness

`EvidenceCompletenessMetric` uses the case `DiscoveryPlan` (or generates one via `PlannerEngine`) to score evidence gaps.

| Score | Condition |
|-------|-----------|
| 100 | All discovery evidence collected |
| 75 | One critical item missing |
| 50 | Multiple critical items missing |
| 0 | No evidence collected |

Critical priorities: `CRITICAL` and `HIGH` on non-optional discovery requests.

Recommendations list the exact missing commands with priority and reason.

## Engine

```python
report = InvestigationQualityEngine().evaluate_case(case)
```

- `overall_score` is the rounded average of registered metric scores
- With only `evidence_completeness` registered, overall score equals completeness score
- `ready_for_recommendation`: overall score ≥ 75
- `ready_for_case_closure`: overall score == 100

## Runtime integration

```python
report = runtime.evaluate_investigation_quality(case_id)
case.investigation_quality_report  # stored on the case aggregate
```

Behavior:

- Ensures a discovery plan exists (generates one if missing)
- Runs `InvestigationQualityEngine.evaluate_case(case)`
- Stores the resulting `InvestigationQualityReport` on `Case.investigation_quality_report`
- Returns the immutable report

## Incident report section

Closed-case reports include:

```markdown
## Investigation Quality
```

When a quality report exists, the section lists overall score, status, readiness flags, per-metric scores, and recommendations.

When no report was generated:

```markdown
_No investigation quality report recorded._
```

## CLI commands

Evaluate quality for an in-memory case:

```bash
voicepilot quality CASE-ID
```

Run a scenario through correlation and print investigation quality:

```bash
voicepilot quality-scenario VP-CUBE-0001 --scenario provider_503
```

Optional investigation quality section in scenario Markdown output:

```bash
voicepilot scenarios VP-CUBE-0001 --scenario provider_503 --output results.md --include-quality
```

## Extensibility

Add a new metric by:

1. Implementing `InvestigationQualityMetric`
2. Registering it in `quality_bootstrap.py` or a custom registry
3. Passing the registry to `InvestigationQualityEngine(registry=...)`

Future metrics automatically contribute to `overall_score` via averaging.

## Limitations

- Cases remain in-memory only; `voicepilot quality CASE-ID` requires a case created in the same process
- v1 ships one built-in metric (`evidence_completeness`)
- Quality evaluation depends on discovery planner output for evidence gap detection

## Tests

```bash
pytest tests/test_investigation_quality_framework.py
pytest
```
