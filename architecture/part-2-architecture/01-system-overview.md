# 01 — System Overview

> **Status:** Partial

## Purpose

Provide a high-level map of VoicePilot components: runtime kernel, engines, plugins, CLI, and the relationship between implemented `core/` modules and documented `brain/` stubs.

## Repository Modules Involved

- [`../../core/runtime/runtime_engine.py`](../../core/runtime/runtime_engine.py)
- [`../../core/runtime/engine_registry.py`](../../core/runtime/engine_registry.py) — brain engine name placeholders
- [`../../cli/voicepilot_cli.py`](../../cli/voicepilot_cli.py)
- [`../../sdk/`](../../sdk/) — plugin SDK

## Related Tests

- [`../../tests/test_runtime_engine.py`](../../tests/test_runtime_engine.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)

## Related Documentation

- [`../../docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md)
- [`../../brain/README.md`](../../brain/README.md)

## Mermaid Diagrams Required

- **System context diagram** — CLI, runtime, engines, plugins, knowledge packs
- **Component dependency overview** — `core/` package relationships

## Cross References

- [02 — Core Platform Layers](02-core-platform-layers.md)
- [06 — Brain Architecture](06-brain-architecture.md)
- [Part 1 — Project Overview](../part-1-foundation/01-project-overview.md)
