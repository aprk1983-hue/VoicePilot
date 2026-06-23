# 01 — REST API

> **Status:** Implemented

## Purpose

Document the VoicePilot Enterprise REST API: a FastAPI orchestration layer that exposes investigation workflows without duplicating engine logic.

## Architecture

```text
Client → FastAPI (api/) → VoicePilotService → RuntimeEngine → Existing Engines
```

REST routers contain **no business logic**. Every mutating and query operation delegates to `VoicePilotService`.

## Repository Modules

- [`../../api/main.py`](../../api/main.py) — application factory, middleware, exception handlers
- [`../../api/dependencies.py`](../../api/dependencies.py) — service dependency injection
- [`../../api/routers/`](../../api/routers/) — thin HTTP adapters
- [`../../api/schemas/`](../../api/schemas/) — Pydantic request/response models
- [`../../core/services/voicepilot_service.py`](../../core/services/voicepilot_service.py) — public facade

## Request Flow

```text
HTTP Request
  → RequestContextMiddleware (request ID, timing log)
  → Router endpoint
  → VoicePilotService method
  → RuntimeEngine / Brain / ValidationEngine
  → DTO mapped to Pydantic response
  → ApiEnvelope { success, data, request_id, timestamp }
```

## Error Flow

```text
ServiceCaseNotFoundError / ServiceBrainSessionNotFoundError / ServicePlaybookNotFoundError
  → 404 JSON error envelope

RequestValidationError → 422 JSON error envelope + details

VoicePilotServiceError → 400 JSON error envelope
```

## OpenAPI

Auto-generated from FastAPI route signatures and Pydantic models:

| URL | UI |
|-----|-----|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | Raw schema |

## Endpoint Matrix

| Area | Endpoints |
|------|-----------|
| Health | `GET /health`, `GET /version` |
| Cases | `POST/GET/DELETE /cases`, `GET /cases/{id}` |
| Evidence | `POST /cases/{id}/evidence` |
| Investigation | `POST /cases/{id}/investigate`, `GET /cases/{id}/status` |
| Brain | `POST /brain/start`, `GET /brain/{session}`, `GET /brain/{session}/timeline` |
| Reports | `GET /cases/{id}/report`, `/executive`, `/engineering`, `/cab` |
| Change Package | `GET /cases/{id}/change-package` |
| Validation | `POST /validate` |

## Constraints

- Read-only investigation (advisory outputs)
- No authentication or tenancy (future)
- In-memory storage only
- No direct RuntimeEngine access from routers

## Related Tests

- [`../../tests/test_api.py`](../../tests/test_api.py)

## Cross References

- [Part 4 — Platform](../part-4-platform/README.md)
- [Sprint 10 Service Layer](../../docs/sprint-10/service-layer-v1.md)
