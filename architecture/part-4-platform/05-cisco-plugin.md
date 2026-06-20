# 05 — Cisco Plugin

> **Status:** Implemented

## Purpose

Document the official Cisco plugin: manifest, VP-CUBE-0001 playbook, Cisco CLI parsers, and registration with the parser engine and playbook catalog.

## Repository Modules Involved

- [`../../plugins/cisco/manifest.yaml`](../../plugins/cisco/manifest.yaml)
- [`../../plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml`](../../plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml)
- [`../../plugins/cisco/parser/`](../../plugins/cisco/parser/) — four Cisco parsers
- [`../../core/runtime/parser_bootstrap.py`](../../core/runtime/parser_bootstrap.py)

## Related Tests

- All `tests/test_cisco_*_parser.py` files
- [`../../tests/test_plugin_registry.py`](../../tests/test_plugin_registry.py)
- [`../../tests/test_playbook_catalog.py`](../../tests/test_playbook_catalog.py)
- [`../../tests/test_demo_runner.py`](../../tests/test_demo_runner.py)

## Related Documentation

- [`../../plugins/cisco/README.md`](../../plugins/cisco/README.md)
- [`../../plugins/cisco/parser/README.md`](../../plugins/cisco/parser/README.md)
- [`../../docs/parsers/`](../../docs/parsers/) — per-parser reference docs
- [`../../docs/playbooks/cube/vp-cube-0001-outbound-calls-fail.md`](../../docs/playbooks/cube/vp-cube-0001-outbound-calls-fail.md)

## Mermaid Diagrams Required

- **Cisco plugin component map** — manifest, playbooks, parsers
- **Cisco parser registration** — `register_cisco_parsers()` → `ParserRegistry`

## Cross References

- [Part 2 — Plugin Architecture](../part-2-architecture/04-plugin-architecture.md)
- [Part 3 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [Part 4 — Knowledge Packs](04-knowledge-packs.md)
- [02 — Demo and Examples](02-demo-and-examples.md)
