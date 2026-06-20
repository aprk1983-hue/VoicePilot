# 03 — AI Integration

> **Status:** Planned

## Purpose

Document planned AI agent integration. The repository includes `ai/` placeholders and brain documentation describing agent roles, but investigation engines in `core/runtime/` are deterministic and do not invoke AI models.

## Repository Modules Involved

- [`../../ai/`](../../ai/) — placeholder (`prompts/`, `reasoning/` — no implementation)
- [`../../sdk/plugin_interface.py`](../../sdk/plugin_interface.py) — `AIProvider` protocol (interface only)
- [`../../brain/`](../../brain/) — AI-related engine documentation stubs
- [`../../docs/architecture/ai-agents.md`](../../docs/architecture/ai-agents.md)

## Related Tests

- None — no AI integration tests exist

## Related Documentation

- [`../../docs/architecture/ai-agents.md`](../../docs/architecture/ai-agents.md)
- [`../../brain/reasoning-engine/README.md`](../../brain/reasoning-engine/README.md)
- [`../../brain/knowledge-engine/README.md`](../../brain/knowledge-engine/README.md)

## Mermaid Diagrams Required

- **Planned AI agent roles map** — from `docs/architecture/ai-agents.md`
- **AI provider plugin boundary** — SDK protocol vs runtime (planned)

## Cross References

- [Part 2 — Brain Architecture](../part-2-architecture/06-brain-architecture.md)
- [05 — Brain Engine Roadmap](05-brain-engine-roadmap.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
