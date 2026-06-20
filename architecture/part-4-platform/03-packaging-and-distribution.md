# 03 — Packaging and Distribution

> **Status:** Implemented

## Purpose

Document Python packaging via `pyproject.toml`, editable install, package discovery roots, console script registration, and pytest configuration.

## Repository Modules Involved

- [`../../pyproject.toml`](../../pyproject.toml)
- Package roots: `core/`, `cli/`, `sdk/`, `plugins/` (via discovery `where = [".", "core"]`)
- [`../../voicepilot.egg-info/`](../../voicepilot.egg-info/) — generated metadata (when installed)

## Related Tests

- [`../../tests/test_packaging.py`](../../tests/test_packaging.py)

## Related Documentation

- [`../../README.md`](../../README.md)

## Mermaid Diagrams Required

- **Package discovery map** — which directories contribute importable packages
- **Install and entry point flow** — `pip install -e .` → `voicepilot` console script

## Cross References

- [01 — CLI](01-cli.md)
- [Part 2 — Plugin Architecture](../part-2-architecture/04-plugin-architecture.md)
