# Architecture Decision Records (ADR)

VoicePilot uses Architecture Decision Records to capture significant structural decisions. **No numbered ADRs exist in the repository yet.** This directory is the canonical location for future ADRs.

## Status

| Item | Status |
|------|--------|
| ADR directory | **Created** (Sprint A1) |
| Numbered ADR files | **None yet** |
| Related RFCs | [`../../docs/product/rfc-001-investigation-engine.md`](../../docs/product/rfc-001-investigation-engine.md) |

## ADR Template

Use the following template when adding a new ADR as `adr/NNNN-short-title.md`:

```markdown
# ADNNNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by ADMMMM

## Context

What problem or constraint led to this decision?

## Decision

What was decided?

## Consequences

Positive and negative outcomes.

## Repository Impact

- Modules affected
- Tests affected
- Documentation updated

## Cross References

- Architecture book chapters
- Sprint docs
- Superseded/superseding ADRs
```

## Candidate Topics (from existing repository decisions)

These topics are inferred from implemented code and sprint docs — **not yet formal ADRs**:

| Topic | Evidence in repository |
|-------|------------------------|
| Deterministic investigation pipeline | `core/runtime/*_engine.py`, sprint-1 docs |
| Parser-first analysis with v1 fallback | `analysis_engine.py`, sprint-2 doc |
| CVOM separation from investigation domain | `core/model/` vs `core/domain/` |
| In-memory persistence v1 | `InMemoryCaseRepository`, sprint-8 snapshot docs |
| Vendor-neutral engines with Cisco plugin | `plugins/cisco/`, `core/parser/` |
| Knowledge packs as repo YAML data | `knowledge/packs/`, packaging exclude rules |
| Package discovery layout | `pyproject.toml` `where = [".", "core"]` |

## Cross References

- [Architecture Book README](../README.md)
- [Diagrams Index](../diagrams/README.md)
- [Part 1 — Design Principles](../part-1-foundation/02-design-principles.md)
