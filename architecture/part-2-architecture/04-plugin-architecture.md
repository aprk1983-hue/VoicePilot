# 04 — Plugin Architecture

> **Status:** Implemented

## Purpose

Document plugin discovery via `manifest.yaml`, the SDK contract (`VoicePilotPlugin`, provider protocols), registry indexing, and playbook catalog integration.

## Repository Modules Involved

- [`../../sdk/plugin_interface.py`](../../sdk/plugin_interface.py) — `VoicePilotPlugin`, provider protocols
- [`../../sdk/plugin_manifest.py`](../../sdk/plugin_manifest.py) — `PluginManifest`
- [`../../sdk/plugin_types.py`](../../sdk/plugin_types.py) — `PluginType`, `PluginCapability`
- [`../../core/runtime/plugin_registry.py`](../../core/runtime/plugin_registry.py)
- [`../../core/runtime/playbook_catalog.py`](../../core/runtime/playbook_catalog.py)
- [`../../plugins/cisco/manifest.yaml`](../../plugins/cisco/manifest.yaml)

## Related Tests

- [`../../tests/test_plugin_registry.py`](../../tests/test_plugin_registry.py)
- [`../../tests/test_plugin_manifest.py`](../../tests/test_plugin_manifest.py)
- [`../../tests/test_playbook_catalog.py`](../../tests/test_playbook_catalog.py)
- [`../../tests/test_packaging.py`](../../tests/test_packaging.py)

## Related Documentation

- [`../../docs/sprint-1/plugin-registry.md`](../../docs/sprint-1/plugin-registry.md)
- [`../../docs/sprint-1/playbook-catalog.md`](../../docs/sprint-1/playbook-catalog.md)
- [`../../plugins/README.md`](../../plugins/README.md)
- [`../../sdk/README.md`](../../sdk/README.md)

## Mermaid Diagrams Required

- **Plugin discovery flow** — filesystem → manifest → registry → catalog
- **SDK provider protocol map** — playbook, parser, knowledge, AI providers

## Cross References

- [Part 1 — VoicePilot DSL](../part-1-foundation/06-voicepilot-dsl.md)
- [Part 4 — Cisco Plugin](../part-4-platform/05-cisco-plugin.md)
- [Part 3 — Parser Engine](../part-3-engines/02-parser-engine.md)
