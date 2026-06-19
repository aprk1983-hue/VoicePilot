# Plugin Registry — Sprint 1

## Purpose

`PluginRegistry` is the VoicePilot Core component that discovers installed plugins from the filesystem and exposes their declared assets — starting with **playbook entry points**.

It bridges the plugin directory layout (`plugins/<name>/manifest.yaml`) and runtime services (`PlaybookLoader`, future `PlaybookEngine`) without embedding vendor logic in core.

## Discovery Flow

```
plugins/                          PluginRegistry.discover()
  cisco/                                │
    manifest.yaml  ─────────────────────┼──► validate required fields
    playbooks/                          │         │
      cube/*.vpb.yaml                   │         ▼
  microsoft/ (future)                   └──► PluginManifest (SDK)
                                              registered by name
                                                    │
                                                    ▼
                                         list_playbook_paths()
```

### Steps

1. **Scan** — Iterate immediate child directories of `plugins_root` (default: `plugins/`).
2. **Filter** — Skip hidden directories and directories without `manifest.yaml`.
3. **Load** — Parse YAML via `YamlLoader` (infrastructure adapter).
4. **Validate** — Enforce required manifest fields and `plugin_type` enum.
5. **Register** — Build `PluginManifest.from_mapping()` and index by `name`.
6. **Expose** — Return playbook paths via `resolve_playbook_paths()` on each manifest.

### Explicit Load

`load_manifest(plugin_dir)` loads a single plugin directory. Raises `PluginManifestNotFoundError` if `manifest.yaml` is missing.

## Manifest Validation

| Field | Required |
|-------|----------|
| `name` | Yes |
| `display_name` | Yes |
| `version` | Yes |
| `vendor` | Yes |
| `plugin_type` | Yes — must be valid `PluginType` enum value |

Optional fields (`capabilities`, `supported_platforms`, `entry_points`, `description`) are passed through to `PluginManifest`.

### Errors

| Exception | When |
|-----------|------|
| `PluginManifestNotFoundError` | `manifest.yaml` missing on explicit load |
| `PluginManifestValidationError` | Missing/invalid fields, duplicate plugin `name` |
| `PluginNotFoundError` | `get(name)` when plugin not registered |

## API Summary

```python
registry = PluginRegistry(plugins_root=Path("plugins"))
registry.discover()

registry.get("cisco")                    # PluginManifest
registry.list_plugins()                  # all manifests
registry.list_playbook_paths()           # all playbook paths
registry.list_playbook_paths_for("cisco")
registry.is_registered("cisco")
```

## Integration Points (Current & Future)

| Consumer | Usage |
|----------|-------|
| `PlaybookLoader` | Load `.vpb.yaml` from paths returned by registry |
| `RuntimeEngine.start()` | TODO — call `discover()` on startup |
| `RuntimeConfig` | `playbooks_path` / plugins root configuration |
| `PlaybookEngine` | TODO — bind playbook by ID from plugin assets |

## Future Marketplace Support

PluginRegistry v1 is filesystem-based and designed for extension:

- **Multiple roots** — official `plugins/` + customer `~/.voicepilot/plugins/` + marketplace cache
- **Signed manifests** — verify publisher signature before `register()`
- **Trust levels** — `official`, `verified`, `community`, `private`
- **Capability index** — `find_by_capability("cube_playbooks")` without scanning YAML each time
- **Version constraints** — reject plugins incompatible with core API version
- **Hot reload** — `rediscover()` for development; immutable registry in production

Marketplace delivery is **not implemented** in Sprint 1. The registry API and `PluginManifest` SDK model are marketplace-ready.

## Related

- [SDK PluginManifest](../../sdk/plugin_manifest.py)
- [Runtime plugin_registry.py](../../core/runtime/plugin_registry.py)
- [Plugins README](../../plugins/README.md)
