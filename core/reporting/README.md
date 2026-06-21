# Enterprise Reporting Engine (ERE)

Vendor-neutral audience-specific reporting for VoicePilot investigations.

## Purpose

Transform existing investigation outputs into multiple report types for different audiences without performing new diagnosis or changing recommendations.

## Read-Only by Design

Reports summarize deterministic investigation results only. VoicePilot never executes configuration changes.

## Report Types

| Type | Audience |
|------|----------|
| `ENGINEERING` | Engineers — wraps existing incident report markdown |
| `EXECUTIVE` | Leadership — business impact and risk summary |
| `CUSTOMER` | Customer-facing — plain language, no CLI terminology |
| `CAB` | Change Advisory Board — change summary, rollback, verification |
| `OPERATIONS` | NOC / operations — health, quality, knowledge, monitoring |

## Modules

| Module | Responsibility |
|--------|----------------|
| `report_models.py` | Frozen dataclasses and `ReportType` enum |
| `report_engine.py` | `EnterpriseReportEngine.generate(case, report_type)` |
| `report_templates.py` | Audience-specific body templates |
| `report_formatter.py` | Markdown assembly with read-only notice |

## Integration

- `RuntimeEngine.generate_audience_report(case_id, report_type)`
- `VoicePilotService.generate_report(case_id, report_type)`
- CLI: `voicepilot report`, `voicepilot report-scenario`

See `docs/sprint-10/enterprise-reporting-engine-v1.md`.
