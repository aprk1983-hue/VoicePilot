# Playbook Catalog — Sprint 1

## Purpose

`PlaybookCatalog` connects **plugin discovery** (`PluginRegistry`) to **playbook loading** (`PlaybookLoader`). It is the runtime index of all DSL playbooks available from installed plugins.

Investigations will bind a case to a cataloged playbook by ID — not by hardcoded filesystem path.

## Flow

```
plugins/cisco/manifest.yaml
        │
        ▼
PluginRegistry.discover()
        │  list_playbook_paths_for("cisco")
        ▼
PlaybookCatalog.load_all()
        │  PlaybookLoader.load(path) per entry point
        ▼
Catalog indexed by playbook_id + plugin_name
        │
        ▼
catalog.get("VP-CUBE-0001")
catalog.list_for_plugin("cisco")
```

## Responsibilities

| Component | Role |
|-----------|------|
| `PluginRegistry` | Discover plugins; expose manifest playbook entry paths |
| `PlaybookLoader` | Parse and validate individual `.vpb.yaml` files |
| `PlaybookCatalog` | Orchestrate loading; index `Playbook` objects |

## API

```python
catalog = PlaybookCatalog(plugin_registry, playbook_loader)

playbooks = catalog.load_all()           # discover plugins + load all
playbook = catalog.get("VP-CUBE-0001") # by DSL metadata ID
cisco = catalog.list_for_plugin("cisco")
entry = catalog.get_entry("VP-CUBE-0001")  # includes plugin + source path
```

## Error Handling

| Exception | When |
|-----------|------|
| `PlaybookIdNotFoundError` | `get()` / `get_entry()` for unknown playbook ID |
| `PluginNotFoundError` | `list_for_plugin()` for unknown plugin |
| `PlaybookCatalogLoadError` | Playbook file missing or fails validation; includes `plugin_name` and `path` |
| `PlaybookValidationError` | Raised by loader; wrapped in `PlaybookCatalogLoadError` during `load_all()` |

## CatalogEntry

Each loaded playbook is stored with provenance:

```python
@dataclass
class CatalogEntry:
    playbook: Playbook
    plugin_name: str
    source_path: Path
```

## RuntimeEngine Integration (Future)

`RuntimeEngine.start()` will:

1. Create `PluginRegistry` from configured `plugins_root`
2. Create `PlaybookCatalog` wired to `PlaybookLoader`
3. Call `catalog.load_all()` to warm the playbook index
4. Pass catalog to investigation startup when binding a case to `VP-CUBE-0001`

## Design Principles

- **No hardcoded paths in core** — all playbook locations come from plugin manifests
- **Separation of concerns** — registry discovers; loader validates; catalog indexes
- **Plugin provenance** — every playbook knows which plugin provided it
- **Clear failures** — invalid plugin playbooks surface as `PlaybookCatalogLoadError`

## Related

- [Plugin Registry](plugin-registry.md)
- [PlaybookCatalog source](../../core/runtime/playbook_catalog.py)
- [Cisco plugin](../../plugins/cisco/README.md)
