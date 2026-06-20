# 04 — Canonical Voice Object Model

> **Status:** Implemented

## Purpose

Document the vendor-neutral Canonical Voice Object Model (CVOM): typed voice objects, relationships, topology container, and object registry produced by parsers and consumed by topology, health, knowledge, and configuration engines.

## Repository Modules Involved

- [`../../core/model/voice_graph.py`](../../core/model/voice_graph.py) — `VoiceObject`, `VoiceRelationship`
- [`../../core/model/voice_topology.py`](../../core/model/voice_topology.py) — `VoiceTopology`
- [`../../core/model/object_registry.py`](../../core/model/object_registry.py) — `ObjectRegistry`
- Typed objects: `sip_ua.py`, `dial_peer.py`, `voice_service.py`, `provider.py`, `device.py`, `interface.py`, etc.

## Related Tests

- [`../../tests/test_voice_object_model.py`](../../tests/test_voice_object_model.py)
- [`../../tests/test_cisco_show_sip_ua_status_parser.py`](../../tests/test_cisco_show_sip_ua_status_parser.py)
- [`../../tests/test_cisco_show_dial_peer_voice_summary_parser.py`](../../tests/test_cisco_show_dial_peer_voice_summary_parser.py)
- [`../../tests/test_cisco_show_run_voice_service_voip_parser.py`](../../tests/test_cisco_show_run_voice_service_voip_parser.py)

## Related Documentation

- [`../../docs/sprint-4/canonical-voice-object-model.md`](../../docs/sprint-4/canonical-voice-object-model.md)
- [`../../docs/sprint-4/parser-to-cvom-sipua.md`](../../docs/sprint-4/parser-to-cvom-sipua.md)
- [`../../docs/sprint-4/parser-to-cvom-dial-peer.md`](../../docs/sprint-4/parser-to-cvom-dial-peer.md)
- [`../../docs/sprint-4/parser-to-cvom-voice-service.md`](../../docs/sprint-4/parser-to-cvom-voice-service.md)

## Mermaid Diagrams Required

- **CVOM type hierarchy** — object types and inheritance from `VoiceObject`
- **Parser-to-CVOM flow** — `ParserResult.voice_objects` into case and topology
- **Relationship model** — `VoiceRelationship` links between objects

## Cross References

- [Part 3 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [Part 3 — Topology Engines](../part-3-engines/03-topology-engines.md)
- [Part 4 — Cisco Plugin](../part-4-platform/05-cisco-plugin.md)
