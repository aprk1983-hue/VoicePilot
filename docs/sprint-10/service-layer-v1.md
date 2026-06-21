# Sprint 10 — VoicePilot Service Layer v1

## Purpose

VoicePilot’s runtime kernel exposes powerful orchestration through `RuntimeEngine`, Brain, Health, Knowledge, Topology, and Report engines. Those components are the right place for investigation logic, but they are not a stable public contract for external clients.

The service layer introduces `VoicePilotService`: a thin facade that future clients can depend on without importing runtime internals directly.

## Architecture

```text
CLI / REST / Web UI / SDK / Automation
                │
                ▼
        VoicePilotService  (facade)
                │
                ▼
          RuntimeEngine
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
 Brain     Health/Knowledge  Reports
```

`VoicePilotService` returns frozen DTO models from `services.service_models`. It does not embed business rules.

## Why the Service Layer Exists

- **Stable API surface** for multiple client types
- **DTO boundaries** instead of leaking domain aggregates
- **Dependency injection** for tests and hosted deployments
- **Future mapping** to REST endpoints, SDK methods, and UI actions without rewriting engines

## What It Does Not Do

The service layer must not:

- parse CLI evidence directly
- diagnose faults
- generate hypotheses with custom rules
- contain Cisco-specific logic
- implement troubleshooting policy

It only forwards calls to existing engines through `RuntimeEngine` (and Brain orchestration where applicable).

## Public Methods

| Method | Returns | Delegates To |
|--------|---------|--------------|
| `create_case(playbook_id)` | `ServiceCaseResult` | `RuntimeEngine.start_investigation()` |
| `upload_evidence(...)` | `ServiceEvidenceResult` | evidence collection flow |
| `analyze_case(case_id)` | `ServiceAnalysisResult` | analyze + hypothesis + correlation |
| `plan_discovery(case_id)` | `ServiceDiscoveryResult` | `RuntimeEngine.plan_discovery()` |
| `evaluate_quality(case_id)` | `ServiceQualityResult` | `RuntimeEngine.evaluate_investigation_quality()` |
| `generate_recommendation(case_id)` | `ServiceRecommendationResult` | `RuntimeEngine.generate_recommendation()` |
| `generate_report(case_id)` | `ServiceReportResult` | `RuntimeEngine.generate_report()` |
| `get_case(case_id)` | `ServiceCaseResult` | case manager |
| `list_cases()` | `list[ServiceCaseResult]` | case manager |
| `start_brain_session(playbook_id)` | `ServiceBrainSessionResult` | Brain orchestration |
| `get_brain_status(session_id)` | `ServiceBrainSessionResult` | Brain registry |
| `replay_brain_session(session_id)` | `str` | Brain replay formatter |

## Example Usage

```python
from services import VoicePilotService

vp = VoicePilotService()

case = vp.create_case("VP-CUBE-0001")

vp.upload_evidence(
    case.case_id,
    "show sip-ua status",
    "... command output ...",
)

analysis = vp.analyze_case(case.case_id)
plan = vp.plan_discovery(case.case_id)
quality = vp.evaluate_quality(case.case_id)
recommendation = vp.generate_recommendation(case.case_id)
report = vp.generate_report(case.case_id)
```

Brain orchestration:

```python
session = vp.start_brain_session("VP-CUBE-0001")
status = vp.get_brain_status(session.session_id)
timeline = vp.replay_brain_session(session.session_id)
```

## Future REST API Mapping

| Service Method | Example REST Route |
|----------------|-------------------|
| `create_case` | `POST /cases` |
| `upload_evidence` | `POST /cases/{id}/evidence` |
| `analyze_case` | `POST /cases/{id}/analyze` |
| `plan_discovery` | `POST /cases/{id}/discovery-plan` |
| `evaluate_quality` | `GET /cases/{id}/quality` |
| `generate_recommendation` | `POST /cases/{id}/recommendation` |
| `generate_report` | `GET /cases/{id}/report` |
| `start_brain_session` | `POST /brain/sessions` |
| `get_brain_status` | `GET /brain/sessions/{id}` |
| `replay_brain_session` | `GET /brain/sessions/{id}/replay` |

## Future SDK Mapping

The SDK can wrap the same DTOs:

```python
client = VoicePilotClient(base_url="https://voicepilot.example")
case = client.cases.create("VP-CUBE-0001")
client.cases.upload_evidence(case.case_id, command="show sip-ua status", content=output)
analysis = client.cases.analyze(case.case_id)
```

## Future UI Mapping

A Web UI can bind screens directly to service DTO fields:

- Case dashboard → `ServiceCaseResult`
- Evidence upload panel → `ServiceEvidenceResult`
- Investigation progress → `ServiceAnalysisResult`, `ServiceDiscoveryResult`, `ServiceQualityResult`
- Recommendation panel → `ServiceRecommendationResult`
- Report viewer → `ServiceReportResult.markdown`
- Brain session monitor → `ServiceBrainSessionResult`

## Current Limitations

- In-memory case storage only (same as current runtime default)
- No persistence, auth, or multi-tenant boundaries yet
- `generate_report()` requires a closed case
- Brain replay/status use in-memory Brain registry unless a future persistence layer is added

## Package Location

- Implementation: `core/services/`
- Import: `from services import VoicePilotService`
