# VoicePilot Web UI

React + Vite + TypeScript frontend for VoicePilot Enterprise.

## Prerequisites

- Node.js 18+
- VoicePilot FastAPI backend running on port 8000

## Run

```bash
# Terminal 1 — backend
cd /path/to/VoicePilot
pip install -e ".[dev]"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd web
npm install
npm run dev
```

Open http://localhost:5173

## Configuration

Optional `.env`:

```
VITE_API_BASE=http://localhost:8000
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm test` | Run Vitest unit tests |

## Pages

- Dashboard
- Cases / New Case / Case Detail
- Evidence Upload
- Investigation Status
- Report Viewer (Executive, Engineering, CAB)
- Change Package Viewer
- Validation

## Constraints

- UI calls REST API only — no business logic
- Read-only investigation principle shown in header/footer
- No authentication (future sprint)
