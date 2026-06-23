# Sprint 15.1 — VoicePilot Enterprise Backend v1

## Purpose

Transform VoicePilot from a CLI-only tool into an enterprise backend platform by adding a FastAPI REST orchestration layer. All investigation logic remains in existing engines; the API delegates exclusively to `VoicePilotService`.

## Architecture

```text
Browser / Client
      ↓
React UI (future)
      ↓
FastAPI Backend (api/)
      ↓
VoicePilotService
      ↓
RuntimeEngine
      ↓
Existing Engines (Hypothesis, Correlation, Discovery, Quality, Reporting, Brain, Validation)
```

**No business logic in REST endpoints.**

## Tech Stack

- FastAPI
- Pydantic v2
- Uvicorn
- Dependency injection via `api.dependencies.get_voicepilot_service`
- OpenAPI / Swagger UI / ReDoc

## Package Layout

```text
api/
├── main.py                 # App factory, exception handlers, middleware
├── dependencies.py         # VoicePilotService DI
├── middleware.py           # Request ID + structured logging
├── responses.py            # Success/error envelopes
├── routers/
│   ├── health.py
│   ├── cases.py
│   ├── evidence.py
│   ├── investigation.py
│   ├── brain.py
│   ├── reports.py
│   ├── change_package.py
│   └── validation.py
└── schemas/
    ├── request_models.py
    └── response_models.py
```

## Endpoints

| Method | Path | Service Method |
|--------|------|----------------|
| GET | `/health` | — |
| GET | `/version` | — |
| POST | `/cases` | `create_case` |
| GET | `/cases` | `list_cases` |
| GET | `/cases/{id}` | `get_case` |
| DELETE | `/cases/{id}` | `delete_case` |
| POST | `/cases/{id}/evidence` | `upload_evidence` |
| POST | `/cases/{id}/investigate` | `investigate_case` |
| GET | `/cases/{id}/status` | `get_investigation_status` |
| POST | `/brain/start` | `start_brain_session` |
| GET | `/brain/{session}` | `get_brain_status` |
| GET | `/brain/{session}/timeline` | `replay_brain_session` |
| GET | `/cases/{id}/report` | `generate_legacy_report` |
| GET | `/cases/{id}/executive` | `generate_report(EXECUTIVE)` |
| GET | `/cases/{id}/engineering` | `generate_report(ENGINEERING)` |
| GET | `/cases/{id}/cab` | `generate_report(CAB)` |
| GET | `/cases/{id}/change-package` | `generate_change_package` |
| POST | `/validate` | `validate_playbook` |

## OpenAPI

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI 3 schema |

## Error Format

```json
{
  "success": false,
  "error": "case_not_found",
  "message": "Case not found: CASE-missing",
  "request_id": "uuid",
  "timestamp": "2026-06-19T12:00:00Z"
}
```

HTTP status mapping:

- `404` — case, brain session, or playbook not found
- `422` — request validation failure
- `400` — other service errors

## Run Locally

```bash
pip install -e ".[dev]"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Service Layer Extensions

Sprint 15.1 adds thin facade methods (no engine rewrites):

- `delete_case(case_id)`
- `get_investigation_status(case_id)`
- `investigate_case(case_id)` — orchestrates analyze, discovery, quality, recommendation, change package
- `validate_playbook(playbook_id | None)`

## Constraints

- Read-only investigation outputs
- No authentication (future sprint)
- No database — in-memory case storage only
- No live device connectivity
- No business logic in REST routers

## Related Tests

- [`../../tests/test_api.py`](../../tests/test_api.py) — 74 API tests

## Related Architecture

- [`../../architecture/part-5/01-rest-api.md`](../../architecture/part-5/01-rest-api.md)
