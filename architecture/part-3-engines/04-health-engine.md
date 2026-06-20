# 04 — Health Engine

> **Status:** Implemented

## Purpose

Document the vendor-neutral health rule framework: built-in rules, rule registry, severity/category models, topology evaluation, scoring, and incident report integration.

## Repository Modules Involved

- [`../../core/health/health_engine.py`](../../core/health/health_engine.py)
- [`../../core/health/builtin_rules.py`](../../core/health/builtin_rules.py)
- [`../../core/health/health_rule_registry.py`](../../core/health/health_rule_registry.py)
- [`../../core/health/health_rule.py`](../../core/health/health_rule.py)
- [`../../core/health/health_report.py`](../../core/health/health_report.py)
- [`../../core/runtime/report_engine.py`](../../core/runtime/report_engine.py) — health section in reports

## Related Tests

- [`../../tests/test_health_engine.py`](../../tests/test_health_engine.py)
- [`../../tests/test_report_engine.py`](../../tests/test_report_engine.py)
- [`../../tests/test_cli_health.py`](../../tests/test_cli_health.py)

## Related Documentation

- [`../../docs/sprint-6/health-framework-v1.md`](../../docs/sprint-6/health-framework-v1.md)
- [`../../docs/sprint-6/health-reporting-v1.md`](../../docs/sprint-6/health-reporting-v1.md)
- [`../../core/health/README.md`](../../core/health/README.md)

## Mermaid Diagrams Required

- **Health evaluation flow** — topology → rules → `HealthReport`
- **Health score calculation** — severity penalties and pass/warn/fail counts

## Cross References

- [03 — Topology Engines](03-topology-engines.md)
- [05 — Knowledge Framework](05-knowledge-framework.md)
- [Part 4 — CLI](../part-4-platform/01-cli.md)
