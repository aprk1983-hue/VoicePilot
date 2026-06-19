# VoicePilot SDK

The VoicePilot SDK defines the **plugin contract** for extending the core platform with vendor playbooks, parsers, knowledge, and optional AI providers.

## Purpose

Third parties and VoicePilot teams ship capabilities as **plugins** instead of patching core. The SDK specifies:

- Manifest format (`manifest.yaml`)
- Base plugin class (`VoicePilotPlugin`)
- Provider protocols (`PlaybookProvider`, `ParserProvider`, `KnowledgeProvider`, `AIProvider`)

## Modules

| Module | Description |
|--------|-------------|
| `plugin_types.py` | `PluginType`, `PluginCapability` enums |
| `plugin_manifest.py` | `PluginManifest`, `PluginEntryPoints` dataclasses |
| `plugin_interface.py` | `VoicePilotPlugin` ABC and provider protocols |

## Plugin Types

| Type | Purpose |
|------|---------|
| `vendor` | Official or third-party vendor playbooks (Cisco, Microsoft, etc.) |
| `parser` | Evidence parsers and signal extractors |
| `knowledge` | Knowledge corpus extensions |
| `ai` | Optional AI augmentation (must not bypass evidence rules) |
| `integration` | ITSM, CMDB, monitoring connectors |
| `custom` | Organization-specific extensions |

## Official vs Third-Party Plugins

| | Official | Third-Party |
|---|----------|-------------|
| Publisher | VoicePilot | Partners / customers |
| Location | `plugins/<vendor>/` | Installed to configured plugin path |
| Review | SME + TAC review | Customer responsibility |
| Support | VoicePilot support matrix | Vendor support |

## Creating a Plugin

1. Create `plugins/<name>/manifest.yaml`
2. Implement `VoicePilotPlugin` (future: `PluginRegistry` loader)
3. Declare `entry_points` for playbooks, parsers, or knowledge
4. Ship playbooks as `.vpb.yaml` under plugin-relative paths

See [Cisco plugin](../plugins/cisco/README.md) for the reference implementation.

## Future: Marketplace

The SDK enables a **VoicePilot Plugin Marketplace** where:

- Plugins are versioned, signed, and capability-tagged
- Customers install plugins without core upgrades
- Marketplace validates manifest schema and compatibility with core API version
- Official plugins are certified; community plugins are labeled accordingly

**Not implemented in this sprint** — manifest + interface only.

## TODO

- `PluginRegistry` in core to discover and load plugins
- Manifest JSON Schema validation
- Plugin signing and trust levels
