# 04 — Knowledge Packs

> **Status:** Implemented

## Purpose

Document bundled YAML knowledge pack data under `knowledge/packs/`, loading via `knowledge_bootstrap.py`, and separation from the VKF Python framework in `core/knowledge/`.

## Repository Modules Involved

- [`../../knowledge/packs/cisco/best-practices/`](../../knowledge/packs/cisco/best-practices/) — YAML pack files
- [`../../core/runtime/knowledge_bootstrap.py`](../../core/runtime/knowledge_bootstrap.py)
- [`../../core/knowledge/`](../../core/knowledge/) — VKF framework (not pack data)

## Related Tests

- [`../../tests/test_knowledge_pack_integration.py`](../../tests/test_knowledge_pack_integration.py)
- [`../../tests/test_knowledge_framework.py`](../../tests/test_knowledge_framework.py)
- [`../../tests/test_packaging.py`](../../tests/test_packaging.py) — confirms packs are repo data, not Python packages

## Related Documentation

- [`../../docs/sprint-7/cisco-knowledge-pack-v1.md`](../../docs/sprint-7/cisco-knowledge-pack-v1.md)
- [`../../docs/sprint-7/knowledge-framework-v1.md`](../../docs/sprint-7/knowledge-framework-v1.md)

## Mermaid Diagrams Required

- **Knowledge pack directory layout** — vendor/category YAML organization
- **Bootstrap load path** — `PACKS_ROOT` → loader → registry

## Cross References

- [Part 3 — Knowledge Framework](../part-3-engines/05-knowledge-framework.md)
- [05 — Cisco Plugin](05-cisco-plugin.md)
