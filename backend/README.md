# VoicePilot Backend

## Purpose

The VoicePilot backend implements the **Runtime Kernel** — the execution platform for VoicePilot DSL investigations. It is not the web application, not AI, and not the Brain engine implementations. It is the architectural foundation that will orchestrate case lifecycle, playbook loading, state transitions, and internal event distribution.

VoicePilot investigates voice incidents like a senior TAC engineer. The Runtime Kernel ensures that investigations are stateful, auditable, and driven by structured canonical objects.

## Architecture

The backend follows **Clean Architecture** and **Hexagonal Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│              use_cases · commands · queries                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Runtime Kernel                          │
│  RuntimeEngine · CaseManager · PlaybookLoader · StateMachine │
│  EventBus · EngineRegistry                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   Domain Layer      Infrastructure        Shared
 models · events    yaml · filesystem     config · types
 enums · ports      logger
```

**Dependency rule:** outer layers depend on inner layers. Domain has no infrastructure imports.

**Event-driven:** `EventBus` publishes domain events (`CaseCreated`, `CaseStateChanged`, `PlaybookLoaded`) for future engine subscribers.

## Folder Layout

| Path | Responsibility |
|------|----------------|
| `runtime/` | Kernel orchestration — case manager, playbook loader, state machine, event bus, engine registry |
| `domain/` | Entities, value objects, enums, domain events, ports (interfaces) |
| `application/` | Use cases, commands, queries — application orchestration |
| `infrastructure/` | Adapters — YAML loader, filesystem repositories, logging |
| `shared/` | Cross-cutting constants, types, configuration |
| `tests/` | Pytest skeletons for kernel components |

## Runtime Kernel Components

| Component | Role |
|-----------|------|
| `RuntimeEngine` | Top-level wiring of kernel services |
| `CaseManager` | Create, load, save, update cases; track state; publish events |
| `PlaybookLoader` | Load `.vpb.yaml`, validate structure, return `Playbook` |
| `InvestigationStateMachine` | Validate lifecycle transitions (12 states) |
| `EventBus` | Internal `subscribe` / `unsubscribe` / `publish` |
| `EngineRegistry` | Register brain engines by name (implementations deferred) |

## Running Tests

```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Future Roadmap

| Phase | Scope |
|-------|--------|
| **Phase 1** (current) | Runtime Kernel skeleton — architecture only |
| **Phase 2** | Case persistence serialization; JSON Schema playbook validation |
| **Phase 3** | DSL rule evaluation pipeline; playbook bind to case |
| **Phase 4** | Brain engine implementations behind `EngineRegistry` |
| **Phase 5** | Investigation execution loop in `RuntimeEngine` |
| **Phase 6** | API layer (FastAPI) and external integrations |
| **Phase 7** | Web UI (out of scope for backend kernel) |

## Related Documentation

- [VoicePilot DSL](../docs/dsl/voicepilot-dsl.md)
- [Canonical Data Model](../docs/data-model/canonical-data-model.md)
- [VoicePilot Brain](../brain/README.md)
