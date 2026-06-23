# Sprint 15.3 — Enterprise Dashboard & Investigation Workspace v1

VoicePilot now includes an enterprise React dashboard and investigation workspace over the FastAPI backend.

## Delivered

- Dashboard summary API: `GET /dashboard/summary`
- Dark/light theme with persistence
- Sidebar navigation and mobile layout
- Dashboard metrics and platform health cards
- Searchable/sortable case grid
- Investigation workspace with tabs:
  - Overview
  - Evidence upload
  - Investigation timeline
  - Reports
  - Change package
- Report tabs for Executive, Engineering, and CAB reports
- Read-only advisory messaging throughout the UI

## Tests

- Frontend: 18 tests
- API: 82 tests
- Dashboard service: 2 tests
- API integration: 2 tests

## Read-only Principle

The UI only calls VoicePilot REST APIs. VoicePilot remains advisory-only and never performs configuration changes or live device connectivity.
