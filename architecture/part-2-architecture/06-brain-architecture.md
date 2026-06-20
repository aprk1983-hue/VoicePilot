# 06 — Brain Architecture

> **Status:** Planned

## Purpose

Document the relationship between the `brain/` documentation stubs (16 planned engines) and the engines actually implemented under `core/runtime/`, `core/topology/`, `core/health/`, and `core/knowledge/`. Clarify what is design intent versus shipped code.

## Repository Modules Involved

- [`../../brain/README.md`](../../brain/README.md) — brain architecture overview
- [`../../brain/*/README.md`](../../brain/) — per-engine documentation stubs
- [`../../core/runtime/engine_registry.py`](../../core/runtime/engine_registry.py) — placeholder brain engine names
- Implemented counterparts in `core/runtime/`, `core/topology/`, `core/health/`, `core/knowledge/`

## Related Tests

- No dedicated `brain/` implementation tests — validate via runtime and engine tests in `tests/`

## Related Documentation

- [`../../docs/architecture/voicepilot-brain.md`](../../docs/architecture/voicepilot-brain.md)
- [`../../docs/architecture/ai-agents.md`](../../docs/architecture/ai-agents.md)
- [`../../brain/README.md`](../../brain/README.md)

## Mermaid Diagrams Required

- **Brain vs core mapping** — planned brain engine → implemented module (where applicable)
- **Future brain topology** — from `brain/README.md` ASCII diagram as Mermaid

## Cross References

- [Part 5 — Brain Engine Roadmap](../part-5-future/05-brain-engine-roadmap.md)
- [Part 2 — System Overview](01-system-overview.md)
- [Part 3 — Engines](../part-3-engines/README.md)
