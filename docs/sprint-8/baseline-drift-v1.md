# Baseline and Drift v1

Sprint 8.3 introduces approved configuration baselines and drift detection against later snapshots.

## Goals

- Mark a snapshot as an approved baseline
- Compare current snapshots against baselines
- Classify drift severity deterministically
- Provide actionable recommendations
- In-memory only; no database, AI, API, or React

## Architecture

```
ConfigurationSnapshot
      ↓
BaselineRegistry.register_baseline()
      ↓
Baseline
      ↓
DriftEngine.compare_to_baseline()
      ↓
DiffEngine.compare()
      ↓
DriftReport
      ↓
format_drift_report_markdown()
```

## Baseline model

| Field | Purpose |
|-------|---------|
| `baseline_id` | Stable baseline identifier (`BASE-*`) |
| `snapshot_id` | Approved snapshot reference |
| `hostname` | Device hostname |
| `approved_by` | Approver identity |
| `approved_at` | Approval timestamp |
| `label` | Short baseline name |
| `description` | Baseline notes |
| `metadata` | Extra baseline metadata |

## Drift status mapping

| Diff risk / changes | Drift status |
|---------------------|--------------|
| No added/removed/modified changes | `NO_DRIFT` |
| Risk `low` or `none` with changes | `LOW_DRIFT` |
| Risk `medium` | `MEDIUM_DRIFT` |
| Risk `high` | `HIGH_DRIFT` |
| Risk `critical` | `CRITICAL_DRIFT` |

## Recommendations

| Drift status | Recommendation |
|--------------|----------------|
| `NO_DRIFT` | No action required. |
| `LOW_DRIFT` | Document change if expected. |
| `MEDIUM_DRIFT` | Review during next maintenance window. |
| `HIGH_DRIFT` | Validate changes against approved change record. |
| `CRITICAL_DRIFT` | Review immediately before production impact. |

## API

```python
from configuration import BaselineRegistry, DriftEngine

registry = BaselineRegistry()
baseline = registry.register_baseline(
    snapshot,
    approved_by="ops-lead",
    label="Approved CUBE baseline",
)

engine = DriftEngine(baseline_registry=registry)
report = engine.compare_to_latest_baseline(current_snapshot, "cube-edge-01")
```

## Example report

```markdown
## Baseline Drift Report

Baseline: BASE-approved (Approved baseline)
Drift Status: CRITICAL_DRIFT

- Review immediately before production impact.

## Configuration Diff
...
```

## Future work

- Baseline approval workflow in CLI and reports
- Scheduled drift checks
- Multi-host baseline catalogs
- Persistent baseline storage

## Tests

```bash
pytest tests/test_baseline_drift_engine.py -v
```

## Related

- [Configuration snapshot v1](./configuration-snapshot-v1.md)
- [Configuration diff v1](./configuration-diff-v1.md)
