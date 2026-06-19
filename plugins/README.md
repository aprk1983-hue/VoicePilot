# VoicePilot Plugins

Plugins extend VoicePilot Core with vendor-specific investigation assets and optional providers.

## Architecture

```
┌─────────────────────────────────────────┐
│           VoicePilot Core               │
│  runtime · domain · application         │
│       PluginRegistry                    │
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

1. `PluginRegistry` scans `plugins/` (configurable root path)
2. Reads each `manifest.yaml` into `PluginManifest` (SDK)
3. Validates required fields (`name`, `display_name`, `version`, `vendor`, `plugin_type`)
4. Exposes playbook entry paths via `list_playbook_paths()`
5. `PlaybookLoader` loads `.vpb.yaml` files by path (today) or via future `PlaybookProvider`

```python
from pathlib import Path
from runtime.plugin_registry import PluginRegistry

registry = PluginRegistry(Path("plugins"))
registry.discover()
paths = registry.list_playbook_paths_for("cisco")
```

Directories without `manifest.yaml` are skipped during discovery.

## Official Plugins

| Plugin | Path | Status |
|--------|------|--------|
| Cisco Voice | `plugins/cisco/` | MVP — VP-CUBE-0001 |

## Third-Party Plugins

Third-party plugins use the same SDK contracts. They should:

- Never modify `core/` source
- Declare capabilities explicitly in `manifest.yaml`
- Keep playbooks as `.vpb.yaml` per [DSL spec](../docs/dsl/voicepilot-dsl.md)
- Respect evidence-first investigation rules

Install to an additional plugins path configured on `PluginRegistry` (future: multiple roots).

## Marketplace Concept (Future)

- Certified plugin bundles with version compatibility matrix
- Customer-private plugin registries for air-gapped deployments
- Capability-based discovery: `registry.find_by_capability("cube_playbooks")`
- Signed manifests and trust levels before registration
- Revenue share model for partner-authored plugins

## Related

- [Plugin Registry spec](../docs/sprint-1/plugin-registry.md)
- [SDK](../sdk/README.md)
- [Cisco plugin](cisco/README.md)
- [DSL specification](../docs/dsl/voicepilot-dsl.md)
