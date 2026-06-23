# VoicePilot Web UI

React + Vite + TypeScript enterprise dashboard and investigation workspace for VoicePilot.

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

## Routes

| Route | Description |
|-------|-------------|
| `/` | Dashboard — platform metrics and health |
| `/cases` | Case management grid |
| `/cases/new` | Create investigation case |
| `/cases/:caseId` | Case workspace overview |
| `/cases/:caseId/evidence` | Drag-and-drop evidence upload |
| `/cases/:caseId/investigation` | Investigation timeline and run |
| `/cases/:caseId/reports/:type` | Report viewer (executive, engineering, cab) |
| `/cases/:caseId/change-package` | Change package viewer |
| `/validation` | Validation suite |

## Features

- Dark/light theme toggle (persisted in localStorage)
- Responsive sidebar layout with mobile menu
- Reusable UI components (cards, metrics, badges, timeline)
- Read-only advisory mode — no configuration changes or live device connectivity

## Constraints

- UI calls REST API only — no business logic
- No authentication (future sprint)
