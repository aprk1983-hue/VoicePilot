# 05 — Knowledge Framework

> **Status:** Implemented

## Purpose

Document the Voice Knowledge Framework (VKF): YAML knowledge packs, schema validation, registry, matcher, engine, bootstrap loading, and report/CLI integration.

## Repository Modules Involved

- [`../../core/knowledge/knowledge_engine.py`](../../core/knowledge/knowledge_engine.py)
- [`../../core/knowledge/knowledge_loader.py`](../../core/knowledge/knowledge_loader.py)
- [`../../core/knowledge/knowledge_registry.py`](../../core/knowledge/knowledge_registry.py)
- [`../../core/knowledge/knowledge_matcher.py`](../../core/knowledge/knowledge_matcher.py)
- [`../../core/knowledge/knowledge_schema.py`](../../core/knowledge/knowledge_schema.py)
- [`../../core/runtime/knowledge_bootstrap.py`](../../core/runtime/knowledge_bootstrap.py)
- Pack data: [`../../knowledge/packs/cisco/best-practices/`](../../knowledge/packs/cisco/best-practices/)

## Related Tests

- [`../../tests/test_knowledge_framework.py`](../../tests/test_knowledge_framework.py)
- [`../../tests/test_knowledge_pack_integration.py`](../../tests/test_knowledge_pack_integration.py)
- [`../../tests/test_report_engine.py`](../../tests/test_report_engine.py)
- [`../../tests/test_cli_health.py`](../../tests/test_cli_health.py)

## Related Documentation

- [`../../docs/sprint-7/knowledge-framework-v1.md`](../../docs/sprint-7/knowledge-framework-v1.md)
- [`../../docs/sprint-7/cisco-knowledge-pack-v1.md`](../../docs/sprint-7/cisco-knowledge-pack-v1.md)
- [`../../core/knowledge/README.md`](../../core/knowledge/README.md)

## Mermaid Diagrams Required

- **VKF load and evaluate pipeline** — YAML → loader → registry → matcher → engine → report
- **Knowledge pack matching rules** — object type, vendor scope, conditions

## Cross References

- [Part 4 — Knowledge Packs](../part-4-platform/04-knowledge-packs.md)
- [04 — Health Engine](04-health-engine.md)
- [07 — Report Engine](07-report-engine.md)
