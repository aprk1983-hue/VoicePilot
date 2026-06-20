# 02 — Core Platform Layers

> **Status:** Partial

## Purpose

Document the hexagonal layering in `core/`: domain, application (CQRS skeleton), infrastructure adapters, shared utilities, and runtime orchestration.

## Repository Modules Involved

- [`../../core/domain/`](../../core/domain/) — entities, ports, events
- [`../../core/application/`](../../core/application/) — `use_cases.py`, `commands.py`, `queries.py`
- [`../../core/infrastructure/`](../../core/infrastructure/) — filesystem repos, YAML loader, logger
- [`../../core/shared/`](../../core/shared/) — constants, types, config
- [`../../core/runtime/`](../../core/runtime/) — orchestration layer
- [`../../core/README.md`](../../core/README.md)

## Related Tests

- [`../../tests/test_case_manager.py`](../../tests/test_case_manager.py)
- [`../../tests/test_playbook_loader.py`](../../tests/test_playbook_loader.py)

## Related Documentation

- [`../../core/README.md`](../../core/README.md)
- [`../../core/domain/README.md`](../../core/domain/README.md) (if present)
- [`../../core/runtime/README.md`](../../core/runtime/README.md) (if present)

## Mermaid Diagrams Required

- **Hexagonal architecture layers** — domain at center, ports, adapters
- **Package dependency direction** — domain ← application ← runtime ← cli

## Cross References

- [03 — Runtime Kernel](03-runtime-kernel.md)
- [Part 1 — Investigation Domain Model](../part-1-foundation/03-investigation-domain-model.md)
