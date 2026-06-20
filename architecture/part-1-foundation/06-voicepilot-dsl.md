# 06 — VoicePilot DSL

> **Status:** Implemented

## Purpose

Document the VoicePilot playbook DSL (`.vpb.yaml`): schema, intake questions, evidence requests, hypothesis templates, verification steps, and how playbooks are loaded and validated.

## Repository Modules Involved

- [`../../core/runtime/playbook_loader.py`](../../core/runtime/playbook_loader.py) — load and validate playbooks
- [`../../core/runtime/playbook_catalog.py`](../../core/runtime/playbook_catalog.py) — index discovered playbooks
- [`../../core/infrastructure/yaml_loader.py`](../../core/infrastructure/yaml_loader.py) — YAML loading
- [`../../core/shared/constants.py`](../../core/shared/constants.py) — `DSL_FILE_EXTENSION`, `DSL_API_VERSION`
- Example playbook: [`../../plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml`](../../plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml)

## Related Tests

- [`../../tests/test_playbook_loader.py`](../../tests/test_playbook_loader.py)
- [`../../tests/test_playbook_catalog.py`](../../tests/test_playbook_catalog.py)
- [`../../tests/test_runtime_engine.py`](../../tests/test_runtime_engine.py)

## Related Documentation

- [`../../docs/dsl/voicepilot-dsl.md`](../../docs/dsl/voicepilot-dsl.md)
- [`../../docs/playbooks/cube/vp-cube-0001-outbound-calls-fail.md`](../../docs/playbooks/cube/vp-cube-0001-outbound-calls-fail.md)
- [`../../docs/sprint-1/playbook-catalog.md`](../../docs/sprint-1/playbook-catalog.md)

## Mermaid Diagrams Required

- **Playbook discovery and load flow** — plugin manifest → catalog → loader → domain `Playbook`
- **DSL structure map** — intake, evidence, hypotheses, verification sections

## Cross References

- [05 — Investigation Lifecycle](05-investigation-lifecycle.md)
- [Part 2 — Plugin Architecture](../part-2-architecture/04-plugin-architecture.md)
- [Part 4 — Cisco Plugin](../part-4-platform/05-cisco-plugin.md)
