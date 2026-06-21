# Enterprise Reporting Engine v1

## Purpose

Sprint 10.8 introduces the **Enterprise Reporting Engine (ERE)** — a vendor-neutral framework that produces audience-specific reports from existing VoicePilot investigation outputs.

ERE transforms data. It does not diagnose, create hypotheses, or modify recommendations.

## Read-Only Design

VoicePilot remains read-only. Every report includes a read-only notice stating that reports summarize investigation results only and do not execute configuration changes.

## Architecture

```text
Case (findings, hypotheses, recommendations, quality, health, change package)
        │
        ▼
build_incident_report() / existing engine outputs  ← no new diagnosis
        │
        ▼
EnterpriseReportEngine.generate(case, report_type)
        │
        ├── report_templates.py  (audience bodies)
        └── report_formatter.py  (metadata + read-only notice)
        │
        ▼
BaseReport subtype (frozen) → markdown
```

## Report Types

| Type | Audience | Content focus |
|------|----------|---------------|
| `ENGINEERING` | Engineers | Wraps existing `format_incident_report()` markdown |
| `EXECUTIVE` | Leadership | Business impact, risk, confidence, next actions |
| `CUSTOMER` | Customers | Plain language, no Cisco CLI terminology |
| `CAB` | Change Advisory Board | Change summary, rollback, verification, approvals |
| `OPERATIONS` | NOC / ops | Health, quality, knowledge matches, monitoring |

## Runtime Integration

```python
# Legacy closed-case incident report (unchanged)
incident = runtime.generate_report(case_id)

# Enterprise audience report (any investigation state with data)
report = runtime.generate_report(case_id, ReportType.EXECUTIVE)
```

## Service Integration

```python
from services import VoicePilotService
from reporting import ReportType

service = VoicePilotService()
result = service.generate_report(case_id, ReportType.EXECUTIVE)
# result.report_id, result.report_type, result.markdown
```

## CLI Usage

```bash
voicepilot report CASE-ID --type engineering
voicepilot report CASE-ID --type executive --output report.md
voicepilot report-scenario VP-CUBE-0001 --scenario sip_ua_disabled --type executive
voicepilot report-scenario VP-CUBE-0001 --scenario sip_ua_disabled --type customer --output customer.md
voicepilot report-scenario VP-CUBE-0001 --scenario sip_ua_disabled --type cab
voicepilot report-scenario VP-CUBE-0001 --scenario sip_ua_disabled --type operations
```

## Example Sections

All reports include:

- Generated timestamp
- Case ID
- Playbook ID
- Report type
- Read-only notice

Engineering reports additionally include all existing incident report sections (findings, CVOM, health, knowledge, correlations, etc.).

## Future Export

- PDF and DOCX rendering from Markdown templates
- ServiceNow incident and change request field mapping
- Scheduled report generation for closed cases
- Trend dashboards for operations reports

## Safety Limitations

- Reports reflect investigation state at generation time
- Customer reports sanitize terminology but engineers must review before external delivery
- CAB reports reuse change package data when available; otherwise summarize existing recommendations
- No connectivity to production systems
