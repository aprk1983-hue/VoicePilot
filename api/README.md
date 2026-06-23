# VoicePilot Enterprise REST API

FastAPI orchestration layer over `VoicePilotService`. REST endpoints contain **no business logic** — they delegate all investigation behavior to the existing service facade and engines.

## Architecture

```text
Browser / Client
      ↓
FastAPI (this package)
      ↓
VoicePilotService
      ↓
RuntimeEngine → Existing Engines
```

## Run Locally

```bash
pip install -e ".[dev]"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentation

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI schema |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API health check |
| GET | `/version` | Platform version |
| POST | `/cases` | Create investigation case |
| GET | `/cases` | List cases |
| GET | `/cases/{id}` | Get case summary |
| DELETE | `/cases/{id}` | Delete case (in-memory) |
| POST | `/cases/{id}/evidence` | Upload evidence |
| POST | `/cases/{id}/investigate` | Run full investigation pipeline |
| GET | `/cases/{id}/status` | Investigation status |
| POST | `/brain/start` | Start Brain session |
| GET | `/brain/{session}` | Brain session status |
| GET | `/brain/{session}/timeline` | Brain replay timeline |
| GET | `/cases/{id}/report` | Legacy incident report |
| GET | `/cases/{id}/executive` | Executive report |
| GET | `/cases/{id}/engineering` | Engineering report |
| GET | `/cases/{id}/cab` | CAB report |
| GET | `/cases/{id}/change-package` | Engineering change package |
| POST | `/validate` | Run validation suite |

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

## Constraints

- Read-only investigation (advisory outputs only)
- No authentication (future sprint)
- In-memory case storage only
- No live device connectivity

## Related

- [`../core/services/README.md`](../core/services/README.md) — VoicePilotService facade
- [`../docs/sprint-15/enterprise-backend-v1.md`](../docs/sprint-15/enterprise-backend-v1.md) — Sprint documentation
- [`../architecture/part-5/01-rest-api.md`](../architecture/part-5/01-rest-api.md) — Architecture chapter
