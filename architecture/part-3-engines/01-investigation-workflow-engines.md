# 01 — Investigation Workflow Engines

> **Status:** Implemented

## Purpose

Document the deterministic investigation pipeline engines: analysis, hypothesis generation, correlation, recommendation, verification, learning, and decision logging — and how `RuntimeEngine` invokes them.

## Repository Modules Involved

- [`../../core/runtime/analysis_engine.py`](../../core/runtime/analysis_engine.py)
- [`../../core/runtime/hypothesis_engine.py`](../../core/runtime/hypothesis_engine.py)
- [`../../core/runtime/correlation_engine.py`](../../core/runtime/correlation_engine.py)
- [`../../core/runtime/recommendation_engine.py`](../../core/runtime/recommendation_engine.py)
- [`../../core/change_package/change_engine.py`](../../core/change_package/change_engine.py) — Engineering Change Package (read-only advisory)
- [`../../core/runtime/verification_engine.py`](../../core/runtime/verification_engine.py)
- [`../../core/runtime/learning_engine.py`](../../core/runtime/learning_engine.py)
- [`../../core/runtime/decision_log_engine.py`](../../core/runtime/decision_log_engine.py)

## Related Tests

- [`../../tests/test_analysis_engine.py`](../../tests/test_analysis_engine.py)
- [`../../tests/test_analysis_engine_parser_integration.py`](../../tests/test_analysis_engine_parser_integration.py)
- [`../../tests/test_hypothesis_engine.py`](../../tests/test_hypothesis_engine.py)
- [`../../tests/test_correlation_engine.py`](../../tests/test_correlation_engine.py)
- [`../../tests/test_recommendation_engine.py`](../../tests/test_recommendation_engine.py)
- [`../../tests/test_verification_engine.py`](../../tests/test_verification_engine.py)
- [`../../tests/test_learning_engine.py`](../../tests/test_learning_engine.py)
- [`../../tests/test_vp_cube_0001_scenarios.py`](../../tests/test_vp_cube_0001_scenarios.py)
- [`../../tests/test_cucm_investigation_engine.py`](../../tests/test_cucm_investigation_engine.py)
- [`../../tests/test_vp_cucm_0001_scenarios.py`](../../tests/test_vp_cucm_0001_scenarios.py)
- [`../../tests/test_validation_engine.py`](../../tests/test_validation_engine.py)

## Related Documentation

- [`../../docs/sprint-1/analysis-v1.md`](../../docs/sprint-1/analysis-v1.md)
- [`../../docs/sprint-1/hypothesis-engine-v1.md`](../../docs/sprint-1/hypothesis-engine-v1.md)
- [`../../docs/sprint-3/correlation-engine-v1.md`](../../docs/sprint-3/correlation-engine-v1.md)
- [`../../docs/sprint-1/recommendation-engine-v1.md`](../../docs/sprint-1/recommendation-engine-v1.md)
- [`../../docs/sprint-10/engineering-change-package-v1.md`](../../docs/sprint-10/engineering-change-package-v1.md)
- [`../../docs/sprint-1/verification-engine-v1.md`](../../docs/sprint-1/verification-engine-v1.md)
- [`../../docs/sprint-1/learning-engine-v1.md`](../../docs/sprint-1/learning-engine-v1.md)
- [`../../docs/sprint-3/decision-log-engine.md`](../../docs/sprint-3/decision-log-engine.md)

## Mermaid Diagrams Required

- **Investigation engine pipeline** — ordered engine execution from analysis to learning
- **Analysis dual-path** — parser-first vs v1 pattern matcher (see existing sprint-2 diagram)

## Cross References

- [Part 1 — Investigation Lifecycle](../part-1-foundation/05-investigation-lifecycle.md)
- [02 — Parser Engine](02-parser-engine.md)
- [07 — Report Engine](07-report-engine.md)
