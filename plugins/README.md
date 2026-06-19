# VoicePilot Plugins

Plugins extend VoicePilot Core with vendor-specific investigation assets and optional providers.

## Architecture

```
┌─────────────────────────────────────────┐
│           VoicePilot Core               │
│  PluginRegistry  →  PlaybookCatalog     │
│       PlaybookLoader                    │
└───────────────────┬─────────────────────┘
                    │ SDK contracts
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   plugins/    third-party   marketplace
   (official)   plugins       (future)
```

## Plugin Directory Structure

```
plugins/
  <plugin-name>/
    manifest.yaml          # Required — plugin metadata and entry points
    README.md
    playbooks/             # Optional — .vpb.yaml DSL playbooks
    parsers/               # Optional — future parser modules
    knowledge/             # Optional — future knowledge packs
```

## How Plugins Load

1. **`PluginRegistry`** scans `plugins/` and reads each `manifest.yaml`
2. **`PlaybookCatalog`** calls `list_playbook_paths()` on registered plugins
3. **`PlaybookLoader`** loads each `.vpb.yaml` into domain `Playbook` objects
4. Runtime looks up playbooks by ID (e.g. `VP-CUBE-0001`) or by plugin name (`cisco`)

```python
from pathlib import Path
from infrastructure.filesystem import FilesystemPlaybookRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry

registry = PluginRegistry(Path("plugins"))
loader = PlaybookLoader(FilesystemPlaybookRepository(YamlLoader()))
catalog = PlaybookCatalog(registry, loader)

catalog.load_all()
playbook = catalog.get("VP-CUBE-0001")
```

No hardcoded playbook paths are required in core — paths come from plugin manifests.

## Official Plugins

| Plugin | Path | Status |
|--------|------|--------|
| Cisco Voice | `plugins/cisco/` | MVP — VP-CUBE-0001 |

## Third-Party Plugins

Third-party plugins use the same SDK contracts. They should:

- Never modify `core/` source
- Declare playbook `entry_points` in `manifest.yaml`
- Keep playbooks as `.vpb.yaml` per [DSL spec](../docs/dsl/voicepilot-dsl.md)
- Respect evidence-first investigation rules

## Marketplace Concept (Future)

- Certified plugin bundles with version compatibility matrix
- Customer-private plugin registries for air-gapped deployments
- Capability-based discovery: `registry.find_by_capability("cube_playbooks")`
- Signed manifests and trust levels before registration

## Related

- [Playbook Catalog](../docs/sprint-1/playbook-catalog.md)
- [Plugin Registry](../docs/sprint-1/plugin-registry.md)
- [SDK](../sdk/README.md)
- [Cisco plugin](cisco/README.md)
- [DSL specification](../docs/dsl/voicepilot-dsl.md)
