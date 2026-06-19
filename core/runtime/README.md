# Runtime Kernel

The runtime package is the VoicePilot execution kernel. It orchestrates case lifecycle, playbook loading, lifecycle state validation, internal events, and engine registration.

## Components

| Module | Responsibility |
|--------|----------------|
| `runtime_engine.py` | Top-level kernel wiring and lifecycle (`start` / `shutdown`) |
| `case_manager.py` | Case aggregate CRUD and state transitions |
| `playbook_loader.py` | Load and structurally validate `.vpb.yaml` playbooks |
| `state_machine.py` | Investigation lifecycle transition validation |
| `event_bus.py` | In-process domain event pub/sub |
| `engine_registry.py` | Brain engine registration (no implementations) |
| `exceptions.py` | Runtime-specific exceptions |

## Design Notes

- **No business logic** in this sprint — engines, reasoning, and DSL execution are TODO.
- **State machine** validates structural transitions only; confidence and evidence gates are future engine responsibilities.
- **Event bus** is synchronous and in-process; no external message broker.

## TODO

- Wire `RuntimeEngine.start()` to playbook discovery
- Replace placeholder engine registrations with real engine classes
- Implement investigation execution pipeline
