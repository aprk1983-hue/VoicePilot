# 02 — Parser Engine

> **Status:** Implemented

## Purpose

Document the vendor-neutral parser framework: command detection, parser registry, parser context/result contracts, and bootstrap of Cisco parsers for runtime analysis.

## Repository Modules Involved

- [`../../core/parser/parser_engine.py`](../../core/parser/parser_engine.py)
- [`../../core/parser/command_detector.py`](../../core/parser/command_detector.py)
- [`../../core/parser/parser_registry.py`](../../core/parser/parser_registry.py)
- [`../../core/parser/interfaces.py`](../../core/parser/interfaces.py) — `CommandParser`
- [`../../core/parser/parser_context.py`](../../core/parser/parser_context.py)
- [`../../core/parser/parser_result.py`](../../core/parser/parser_result.py)
- [`../../core/runtime/parser_bootstrap.py`](../../core/runtime/parser_bootstrap.py)

## Related Tests

- [`../../tests/test_parser_framework.py`](../../tests/test_parser_framework.py)
- [`../../tests/test_cisco_show_sip_ua_status_parser.py`](../../tests/test_cisco_show_sip_ua_status_parser.py)
- [`../../tests/test_cisco_show_dial_peer_voice_summary_parser.py`](../../tests/test_cisco_show_dial_peer_voice_summary_parser.py)
- [`../../tests/test_cisco_show_run_voice_service_voip_parser.py`](../../tests/test_cisco_show_run_voice_service_voip_parser.py)
- [`../../tests/test_cisco_debug_ccsip_messages_parser.py`](../../tests/test_cisco_debug_ccsip_messages_parser.py)

## Related Documentation

- [`../../docs/parser-framework.md`](../../docs/parser-framework.md) — **contains existing Mermaid diagram**
- [`../../docs/sprint-2/parser-analysis-integration.md`](../../docs/sprint-2/parser-analysis-integration.md) — **contains existing Mermaid diagram**
- [`../../docs/parsers/`](../../docs/parsers/) — Cisco parser reference docs

## Mermaid Diagrams Required

- **Parser pipeline** — exists in [`../../docs/parser-framework.md`](../../docs/parser-framework.md); migrate or reference here
- **Parser bootstrap at runtime** — `parser_bootstrap.py` → Cisco registry → `AnalysisEngine`

## Cross References

- [Part 1 — Canonical Voice Object Model](../part-1-foundation/04-canonical-voice-object-model.md)
- [01 — Investigation Workflow Engines](01-investigation-workflow-engines.md)
- [Part 4 — Cisco Plugin](../part-4-platform/05-cisco-plugin.md)
