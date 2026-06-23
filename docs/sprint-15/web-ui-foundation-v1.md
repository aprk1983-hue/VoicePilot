# Sprint 15.2 — VoicePilot Web UI Foundation v1

## Purpose

Deliver the first React web UI for VoicePilot Enterprise. The UI is a thin client over the existing FastAPI backend — no investigation engines or business logic in the frontend.

## Architecture

```text
Browser (web/)
      ↓ fetch / REST
FastAPI (api/) :8000
      ↓
VoicePilotService
      ↓
RuntimeEngine → Existing Engines
```

## Tech Stack

- React 19
- Vite 6
- TypeScript
- React Router 7
- fetch API client (no Axios)
- Basic CSS (no Tailwind)

## Package Layout

```text
web/
├── src/
│   ├── api/           # client.ts, types.ts
│   ├── components/    # Layout, LoadingState, ErrorBanner, MarkdownViewer
│   ├── hooks/         # useAsync
│   ├── pages/         # Dashboard, Cases, CaseDetail, …
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

## Pages

| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/cases` | Cases list |
| `/cases/new` | New Case |
| `/cases/:id` | Case Detail |
| `/cases/:id/evidence` | Evidence Upload |
| `/cases/:id/status` | Investigation Status |
| `/cases/:id/reports/:type` | Report Viewer |
| `/cases/:id/change-package` | Change Package Viewer |
| `/validation` | Validation |

## API Client Methods

- `getHealth`, `getVersion`
- `createCase`, `listCases`, `getCase`, `deleteCase`
- `uploadEvidence`
- `investigateCase`, `getInvestigationStatus`
- `getExecutiveReport`, `getEngineeringReport`, `getCabReport`
- `getChangePackage`
- `validate`

## Run Locally

```bash
# Backend
uvicorn api.main:app --reload --port 8000

# Frontend
cd web && npm install && npm run dev
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Backend Change

Sprint 15.2 adds CORS middleware to `api/main.py` for local Vite dev origins — no engine changes.

## Constraints

- No authentication
- No database
- No business logic in UI
- Read-only principle visible in header/footer

## Related Tests

- `web/src/api/client.test.ts`
- `web/src/App.test.tsx`
- Backend: `tests/test_api.py`

## Related Documentation

- [`../architecture/part-5/01-rest-api.md`](../architecture/part-5/01-rest-api.md)
- [`enterprise-backend-v1.md`](enterprise-backend-v1.md)
