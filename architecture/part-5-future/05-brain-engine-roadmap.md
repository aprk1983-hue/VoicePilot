# 05 — Brain Engine Roadmap

> **Status:** Planned

## Purpose

Catalog the 16 brain engines documented under `brain/` and map each to its implementation status in the current repository.

## Repository Modules Involved

Documentation stubs under [`../../brain/`](../../brain/):

| Brain folder | Documented engine |
|--------------|-------------------|
| `investigation-engine/` | Investigation orchestration |
| `reasoning-engine/` | Reasoning / RCA |
| `evidence-engine/` | Evidence management |
| `hypothesis-engine/` | Hypothesis graph |
| `confidence-engine/` | Confidence scoring |
| `decision-engine/` | Decision support |
| `question-engine/` | Question generation |
| `playbook-engine/` | Playbook execution |
| `learning-engine/` | Learning capture |
| `report-engine/` | Report generation |
| `timeline-engine/` | Timeline construction |
| `topology-engine/` | Topology modeling |
| `knowledge-engine/` | Organizational knowledge |
| `investigation-graph/` | Investigation graph |
| `investigation-planner/` | Investigation planning |
| `cost-optimizer/` | Cost optimization |
| `state-machine/` | Lifecycle state machine |

Implemented partial counterparts exist in `core/runtime/`, `core/topology/`, `core/health/`, `core/knowledge/`, `core/configuration/`.

## Related Tests

- Map each implemented brain area to tests listed in [Part 3 — Engines](../part-3-engines/README.md)

## Related Documentation

- [`../../brain/README.md`](../../brain/README.md)
- Per-engine README files under [`../../brain/`](../../brain/)

## Mermaid Diagrams Required

- **Brain engine maturity matrix** — planned vs implemented vs partial
- **Target brain architecture** — from `brain/README.md` (convert ASCII to Mermaid)

## Cross References

- [Part 2 — Brain Architecture](../part-2-architecture/06-brain-architecture.md)
- [Part 3 — Engines](../part-3-engines/README.md)
- [03 — AI Integration](03-ai-integration.md)
