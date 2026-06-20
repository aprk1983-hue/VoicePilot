# 01 — CLI

> **Status:** Implemented

## Purpose

Document the `voicepilot` console application: bootstrap import paths, investigation command, decisions command, and health assessment with optional Markdown export.

## Repository Modules Involved

- [`../../cli/voicepilot_cli.py`](../../cli/voicepilot_cli.py)
- [`../../cli/__init__.py`](../../cli/__init__.py)
- Console entry: `voicepilot = cli.voicepilot_cli:main` in [`../../pyproject.toml`](../../pyproject.toml)

## Related Tests

- [`../../tests/test_cli.py`](../../tests/test_cli.py)
- [`../../tests/test_cli_health.py`](../../tests/test_cli_health.py)
- [`../../tests/test_packaging.py`](../../tests/test_packaging.py)

## Related Documentation

- [`../../docs/sprint-1/cli-v1.md`](../../docs/sprint-1/cli-v1.md)
- [`../../docs/sprint-7/health-cli-v1.md`](../../docs/sprint-7/health-cli-v1.md)
- [`../../docs/sprint-7/health-cli-export-v1.md`](../../docs/sprint-7/health-cli-export-v1.md)
- [`../../cli/README.md`](../../cli/README.md)

## Mermaid Diagrams Required

- **CLI command map** — subcommands and runtime dependencies
- **Health CLI pipeline** — samples → parsers → topology → health + knowledge → terminal/file output

## Cross References

- [Part 2 — Runtime Kernel](../part-2-architecture/03-runtime-kernel.md)
- [Part 3 — Health Engine](../part-3-engines/04-health-engine.md)
- [03 — Packaging and Distribution](03-packaging-and-distribution.md)
