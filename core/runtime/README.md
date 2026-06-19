# Runtime Kernel

The runtime package is the VoicePilot execution kernel. It orchestrates case lifecycle, playbook loading, plugin discovery, lifecycle state validation, internal events, engine registration, and the v1 investigation intake loop.

## Components

| Module | Responsibility |
|--------|----------------|
| `runtime_engine.py` | Top-level kernel wiring, `start_investigation`, `submit_answer` |
| `intake_flow.py` | Deterministic intake question parsing and turn building |
| `case_manager.py` | Case aggregate CRUD and state transitions |
| `playbook_loader.py` | Load and structurally validate `.vpb.yaml` playbooks |
| `plugin_registry.py` | Discover plugins and expose manifest playbook entry points |
| `playbook_catalog.py` | Load plugin playbooks into a searchable catalog |
| `state_machine.py` | Investigation lifecycle transition validation |
| `event_bus.py` | In-process domain event pub/sub |
| `engine_registry.py` | Brain engine registration (no implementations) |
| `exceptions.py` | Runtime-specific exceptions |

## Runtime Engine v1

v1 implements a **deterministic intake question flow** only. No reasoning, evidence evaluation, or confidence gates yet.

```python
from pathlib import Path
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

engine = RuntimeEngine(
    config=RuntimeConfig(playbooks_path=Path("plugins")),
    case_repository=InMemoryCaseRepository(),
    playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
)
engine.start()

turn = engine.start_investigation("VP-CUBE-0001")
print(turn.prompt)  # first intake question

turn = engine.submit_answer(turn.case_id, turn.question_id, "yes")
```

See [Runtime Engine v1](../../docs/sprint-1/runtime-engine-v1.md) for full behavior and `InvestigationTurn` fields.

## Plugin → Playbook Flow

```
PluginRegistry.discover()
        │
        ▼
list_playbook_paths() / list_playbook_paths_for(name)
        │
        ▼
PlaybookCatalog.load_all()
        │
        ▼
PlaybookLoader.load(path)  →  Playbook objects indexed by ID
        │
        ▼
RuntimeEngine.start_investigation(playbook_id)
```

```python
from pathlib import Path
from infrastructure.filesystem import FilesystemPlaybookRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry

registry = PluginRegistry(plugins_root=Path("plugins"))
loader = PlaybookLoader(FilesystemPlaybookRepository(YamlLoader()))
catalog = PlaybookCatalog(registry, loader)

catalog.load_all()
playbook = catalog.get("VP-CUBE-0001")
cisco_playbooks = catalog.list_for_plugin("cisco")
```

See [Plugin Registry](../../docs/sprint-1/plugin-registry.md) and [Playbook Catalog](../../docs/sprint-1/playbook-catalog.md).

## Design Notes

- **v1 scope:** intake questions from playbook DSL, answer storage, timeline events, state `INTAKE` → `DISCOVERY`.
- **State machine** validates structural transitions only; confidence and evidence gates are future engine responsibilities.
- **Event bus** is synchronous and in-process; no external message broker.

## TODO

- Discovery, topology, and collection execution loops
- Replace placeholder engine registrations with real engine classes
- Evidence parsing, reasoning, and confidence integration
