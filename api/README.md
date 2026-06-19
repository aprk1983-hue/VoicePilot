# VoicePilot API

HTTP API for VoicePilot (future).

## Planned Surface

| Area | Description |
|------|-------------|
| Cases | CRUD, state transitions, evidence submission |
| Playbooks | List, load, bind to case |
| Plugins | List installed plugins |
| Reports | Generate investigation deliverables |

## Status

**Not implemented.** No FastAPI in this sprint.

## Design Notes

- API layer maps REST resources to canonical data model objects
- API will not expose free-text root cause endpoints
- Authentication, tenancy, and rate limiting are future platform concerns
- API package will live alongside `core/` when implemented

## Related

- [Canonical Data Model](../docs/data-model/canonical-data-model.md) — future API mapping section
