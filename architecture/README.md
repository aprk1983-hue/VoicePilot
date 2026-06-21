# VoicePilot Architecture Book

Enterprise architecture documentation for the VoicePilot platform. This book describes the **architecture that exists in the repository** — it is not a design specification for unreleased work.

## How to Use This Book

| Part | Focus |
|------|-------|
| [Part 1 — Foundation](part-1-foundation/README.md) | Domain model, CVOM, lifecycle, DSL |
| [Part 2 — Architecture](part-2-architecture/README.md) | System structure, runtime kernel, plugins |
| [Part 3 — Engines](part-3-engines/README.md) | Implemented analysis, topology, health, knowledge, configuration engines |
| [Part 4 — Platform](part-4-platform/README.md) | CLI, demos, packaging, plugins, knowledge packs |
| [Part 5 — Future](part-5-future/README.md) | Planned capabilities documented elsewhere but not implemented in code |
| [Diagrams](diagrams/README.md) | Required and existing Mermaid diagrams |
| [ADR](adr/README.md) | Architecture Decision Record index and template |

## Source of Truth

- **Implementation:** `core/`, `cli/`, `sdk/`, `plugins/`, `knowledge/`
- **Sprint documentation:** `docs/sprint-*`
- **Brain orchestrator (implemented):** `core/brain/`
- **Brain design stubs (extended engines):** `brain/`
- **Tests:** `tests/`

## Documentation Status Legend

| Status | Meaning |
|--------|---------|
| **Implemented** | Production code and tests exist in the repository |
| **Partial** | Some code exists; book chapter not yet written |
| **Planned** | Documented intent only; no matching implementation |

## Current Platform Snapshot

VoicePilot v0.1.0 is a deterministic, vendor-neutral voice operations investigation platform. The implemented kernel orchestrates playbook-driven investigations through intake, evidence collection, analysis, hypothesis generation, correlation, recommendation, verification, learning, and incident reporting. Extended engines cover CLI parsing, canonical voice topology, health rules, knowledge packs, and configuration snapshot/diff/drift.

## Cross-References

- Platform README: [`../README.md`](../README.md)
- Core platform overview: [`../core/README.md`](../core/README.md)
- Brain orchestrator: [`../core/brain/README.md`](../core/brain/README.md)
- Brain design stubs: [`../brain/README.md`](../brain/README.md)
- Sprint documentation index: [`../docs/`](../docs/)
