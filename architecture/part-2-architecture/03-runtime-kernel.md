# 03 — Runtime Kernel

> **Status:** Implemented

## Purpose

Document `RuntimeEngine` as the top-level orchestrator: investigation start, answer submission, evidence analysis pipeline hooks, report generation, and integration with case management and playbook catalog.

## Repository Modules Involved

- [`../../core/runtime/runtime_engine.py`](../../core/runtime/runtime_engine.py)
- [`../../core/runtime/case_manager.py`](../../core/runtime/case_manager.py)
- [`../../core/runtime/playbook_catalog.py`](../../core/runtime/playbook_catalog.py)
- [`../../core/runtime/plugin_registry.py`](../../core/runtime/plugin_registry.py)
- [`../../core/runtime/__init__.py`](../../core/runtime/__init__.py) — public exports

## Related Tests

- [`../../tests/test_runtime_engine.py`](../../tests/test_runtime_engine.py)
- [`../../tests/test_case_manager.py`](../../tests/test_case_manager.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)
- [`../../tests/test_report_engine.py`](../../tests/test_report_engine.py)

## Related Documentation

- [`../../docs/sprint-1/runtime-engine-v1.md`](../../docs/sprint-1/runtime-engine-v1.md)
- [`../../core/runtime/README.md`](../../core/runtime/README.md)

## Mermaid Diagrams Required

- **RuntimeEngine orchestration sequence** — method calls through investigation lifecycle
- **Runtime component map** — engine dependencies from `RuntimeEngine`

## Cross References

- [04 — Plugin Architecture](04-plugin-architecture.md)
- [05 — State and Events](05-state-and-events.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
- [Part 4 — CLI](../part-4-platform/01-cli.md)
