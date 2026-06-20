# 07 — Report Engine

> **Status:** Implemented

## Purpose

Document deterministic incident report generation from closed cases: case overview, findings, CVOM objects, call paths, health assessment, matched knowledge, correlations, decision timeline, verification, and learning record.

## Repository Modules Involved

- [`../../core/runtime/report_engine.py`](../../core/runtime/report_engine.py)
- Integrations: `TopologyBuilder`, `CallPathEngine`, `HealthEngine`, `default_knowledge_engine()`

## Related Tests

- [`../../tests/test_report_engine.py`](../../tests/test_report_engine.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)

## Related Documentation

- [`../../docs/sprint-1/report-engine-v1.md`](../../docs/sprint-1/report-engine-v1.md)
- [`../../docs/sprint-5/call-path-reporting-v1.md`](../../docs/sprint-5/call-path-reporting-v1.md)
- [`../../docs/sprint-6/health-reporting-v1.md`](../../docs/sprint-6/health-reporting-v1.md)
- [`../../brain/report-engine/README.md`](../../brain/report-engine/README.md) — planned brain doc

## Mermaid Diagrams Required

- **Report section assembly** — case fields and engine outputs → `IncidentReport` → Markdown
- **Report data sources map** — which engines feed each report section

## Cross References

- [01 — Investigation Workflow Engines](01-investigation-workflow-engines.md)
- [03 — Topology Engines](03-topology-engines.md)
- [04 — Health Engine](04-health-engine.md)
- [05 — Knowledge Framework](05-knowledge-framework.md)
- [Part 4 — Demo and Examples](../part-4-platform/02-demo-and-examples.md)
