# 02 — Design Principles

> **Status:** Partial

## Purpose

Document the non-negotiable design principles observable in the implemented codebase: determinism, vendor neutrality, immutability of CVOM objects, separation of parser output from case mutation, and in-memory v1 scope.

## Repository Modules Involved

- [`../../core/model/`](../../core/model/) — immutable CVOM dataclasses
- [`../../core/parser/parser_engine.py`](../../core/parser/parser_engine.py) — domain-pure parsing (no case mutation)
- [`../../core/shared/constants.py`](../../core/shared/constants.py) — shared identifiers and thresholds
- [`../../brain/README.md`](../../brain/README.md) — stated brain design principles (documentation)

## Related Tests

- [`../../tests/test_voice_object_model.py`](../../tests/test_voice_object_model.py) — CVOM immutability
- [`../../tests/test_configuration_diff_engine.py`](../../tests/test_configuration_diff_engine.py) — deterministic diff ordering
- [`../../tests/test_snapshot_engine.py`](../../tests/test_snapshot_engine.py) — deterministic snapshot hashing

## Related Documentation

- [`../../brain/README.md`](../../brain/README.md) — design principles section
- [`../../docs/sprint-4/canonical-voice-object-model.md`](../../docs/sprint-4/canonical-voice-object-model.md)

## Mermaid Diagrams Required

- **Design constraint map** — determinism, vendor neutrality, immutability, no-AI-v1

## Cross References

- [03 — Investigation Domain Model](03-investigation-domain-model.md)
- [04 — Canonical Voice Object Model](04-canonical-voice-object-model.md)
- [Part 3 — Engines](../part-3-engines/README.md)
