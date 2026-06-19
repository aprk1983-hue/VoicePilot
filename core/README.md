# VoicePilot Core

VoicePilot Core is the platform kernel that executes DSL investigations. It contains the runtime engine, domain model, application use cases, infrastructure adapters, and shared utilities — with **no vendor-specific logic**.

## Purpose

Core provides:

- Investigation case lifecycle (`CaseManager`)
- DSL playbook loading (`PlaybookLoader`)
- Lifecycle state validation (`InvestigationStateMachine`)
- Internal event bus (`EventBus`)
- Brain engine registration (`EngineRegistry`)
- Canonical domain entities aligned with the [Canonical Data Model](../docs/data-model/canonical-data-model.md)

Core does **not** include Cisco playbooks, parsers, AI, HTTP APIs, or CLI tools. Those live in **plugins**, **api**, and **cli**.

## Layout

| Path | Responsibility |
|------|----------------|
| `runtime/` | Kernel orchestration |
| `domain/` | Entities, events, enums, ports |
| `application/` | Use cases, commands, queries |
| `infrastructure/` | YAML, filesystem, logging adapters |
| `shared/` | Constants, types, configuration |

## Architecture

Clean / Hexagonal architecture:

```
application → runtime → domain ← infrastructure
```

Plugins integrate via the [VoicePilot SDK](../sdk/README.md) without modifying core source.

## Running Tests

From repository root:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

`PYTHONPATH` includes `core/` via root `pyproject.toml`.

## Backward Compatibility

Legacy `backend/` remains as a compatibility entry point. New development should import from packages under `core/` with repository-root `pytest` configuration.

## Related

- [Platform overview](../README.md) (if present)
- [SDK](../sdk/README.md)
- [Plugins](../plugins/README.md)
- [Brain architecture](../brain/README.md)
