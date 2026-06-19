# Runtime Kernel

The runtime package is the VoicePilot execution kernel. It orchestrates case lifecycle, playbook loading, plugin discovery, lifecycle state validation, internal events, and engine registration.

## Components

| Module | Responsibility |
|--------|----------------|
| `runtime_engine.py` | Top-level kernel wiring and lifecycle (`start` / `shutdown`) |
| `case_manager.py` | Case aggregate CRUD and state transitions |
| `playbook_loader.py` | Load and structurally validate `.vpb.yaml` playbooks |
| `plugin_registry.py` | Discover plugins and expose manifest playbook entry points |
| `playbook_catalog.py` | Load plugin playbooks into a searchable catalog |
| `state_machine.py` | Investigation lifecycle transition validation |
| `event_bus.py` | In-process domain event pub/sub |
| `engine_registry.py` | Brain engine registration (no implementations) |
| `exceptions.py` | Runtime-specific exceptions |

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

- **No business logic** in this sprint — engines, reasoning, and DSL execution are TODO.
- **State machine** validates structural transitions only; confidence and evidence gates are future engine responsibilities.
- **Event bus** is synchronous and in-process; no external message broker.

## TODO

- Wire `RuntimeEngine.start()` to `PlaybookCatalog.load_all()`
- Replace placeholder engine registrations with real engine classes
- Implement investigation execution pipeline
