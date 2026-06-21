# 07 — Report Engine

> **Status:** Implemented

## Purpose

Document deterministic incident report generation from closed cases and the Enterprise Reporting Engine (ERE) for audience-specific commercial reports.

## Repository Modules Involved

- [`../../core/runtime/report_engine.py`](../../core/runtime/report_engine.py) — legacy engineering incident report
- [`../../core/reporting/report_engine.py`](../../core/reporting/report_engine.py) — Enterprise Reporting Engine (ERE)
- [`../../core/reporting/report_templates.py`](../../core/reporting/report_templates.py) — executive, customer, CAB, operations templates
- Integrations: `TopologyBuilder`, `CallPathEngine`, `HealthEngine`, `default_knowledge_engine()`, `EnterpriseReportEngine`

## Enterprise Reporting Engine

ERE produces commercial and operational report types without new diagnosis:

| Report Type | Audience |
|-------------|----------|
| Engineering | Engineers (wraps legacy incident report) |
| Executive | Leadership |
| Customer | Customer-facing summaries |
| CAB | Change Advisory Board |
| Operations | NOC / monitoring |

See [`../../docs/sprint-10/enterprise-reporting-engine-v1.md`](../../docs/sprint-10/enterprise-reporting-engine-v1.md).

## Related Tests

- [`../../tests/test_report_engine.py`](../../tests/test_report_engine.py)
- [`../../tests/test_reporting_engine.py`](../../tests/test_reporting_engine.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)

## Related Documentation

- [`../../docs/sprint-1/report-engine-v1.md`](../../docs/sprint-1/report-engine-v1.md)
- [`../../docs/sprint-10/enterprise-reporting-engine-v1.md`](../../docs/sprint-10/enterprise-reporting-engine-v1.md)
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
