# Enterprise Validation Suite v1

## Purpose

Sprint 11.4 delivers an enterprise-grade validation layer that proves VoicePilot investigations are deterministic, repeatable, and accurate across supported playbooks. The validation engine **never performs investigation logic** — it runs the existing `RuntimeEngine` pipeline and compares outputs to scenario expectations.

## Package

`core/validation/`

| Module | Role |
|--------|------|
| `validation_models.py` | Immutable `ValidationScenario`, `ValidationResult`, `ValidationSuite`, `ValidationSummary`, `ScenarioExpectation`, `ValidationMetrics` |
| `validation_engine.py` | `ValidationEngine` orchestration |
| `validation_rules.py` | Deterministic expectation checks |
| `validation_report.py` | Markdown suite reports |

## Supported Playbooks

| Playbook | Scenarios |
|----------|-----------|
| `VP-CUBE-0001` | 5 standalone scenarios |
| `VP-CUCM-0001` | 5 standalone scenarios |

## Pipeline

```
Scenario evidence
      ↓
RuntimeEngine (existing)
      ↓
Health / Hypotheses / Knowledge / Recommendations / Reports / Change Package / Discovery
      ↓
ValidationEngine
      ↓
PASS / FAIL
```

## Validation Rules

Each scenario's `expected_result.yaml` drives validation:

| Rule | Default |
|------|---------|
| Expected root cause | Required |
| Minimum confidence | Required |
| Expected health status | Optional |
| Expected critical findings | Optional |
| Expected knowledge IDs | Optional |
| Expected runbook IDs | Optional |
| Expected verification IDs | Optional |
| Change package present | `true` |
| Report generated | `true` |
| Recommendation present | `true` |
| Minimum quality score | Optional |
| Minimum health score | Optional |

Extended fields are optional — existing scenario packs continue to work with root-cause and confidence checks only.

## Metrics Captured

- Execution time (ms)
- Confidence
- Investigation quality score
- Knowledge match count
- Health score
- Report size (bytes)
- Topology object count
- Discovery command count
- Critical finding signals

## CLI

```bash
# Validate all supported playbooks
voicepilot validate

# Validate one playbook
voicepilot validate VP-CUBE-0001
voicepilot validate VP-CUCM-0001

# Write Markdown report
voicepilot validate --output validation.md
voicepilot validate VP-CUCM-0001 --output cucm-validation.md
```

## Regression

Validation fails when:

- Root cause does not match expectation
- Confidence is below threshold
- Recommendation is missing (when required)
- Report is missing (when required)
- Change package is missing or empty (when required)
- Expected knowledge, runbook, or verification IDs are absent
- Expected critical finding signals are absent

## Tests

`tests/test_validation_engine.py` covers engine execution, CLI, performance metrics, regression detection, and Markdown reporting.

## Related Documentation

- [Architecture — Enterprise Validation Engine](../../architecture/part-3-engines/09-enterprise-validation-engine.md)
- [CUCM Investigation Engine v1](cucm-investigation-engine-v1.md)
- [Scenario CLI v1](../sprint-9/scenario-cli-v1.md)
