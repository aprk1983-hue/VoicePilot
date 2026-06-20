# Voice Knowledge Framework v1

Sprint 7.1 introduces the Voice Knowledge Framework (VKF) — a vendor-neutral layer for loading, validating, registering, and evaluating structured knowledge packs.

## Goals

- Keep vendor knowledge out of core code
- Load YAML knowledge packs at runtime
- Match packs to Canonical Voice Objects deterministically
- Produce actionable knowledge reports
- No AI, API, React, or persistence changes

## Architecture

```
YAML Knowledge Pack
      ↓
KnowledgeLoader + schema validation
      ↓
KnowledgeRegistry
      ↓
KnowledgeMatcher
      ↓
KnowledgeEngine.evaluate_*()
      ↓
KnowledgeReport
```

## Core models

### KnowledgeSeverity

`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### KnowledgeCategory

`BEST_PRACTICE`, `BUG`, `SECURITY`, `DESIGN`, `CONFIGURATION`, `PERFORMANCE`, `COMPATIBILITY`, `LICENSING`, `OPERATIONS`, `GENERAL`

### KnowledgePack

| Field | Purpose |
|-------|---------|
| `id` | Stable pack identifier |
| `title` | Short name |
| `description` | Pack intent |
| `vendor` / `platform` | Scope filters (`*` matches all) |
| `category` / `severity` | Classification |
| `supported_object_types` | Applicable CVOM types |
| `conditions` | Field conditions for matching |
| `recommendations` | Guidance text |
| `references` | External references |
| `metadata` | Extra pack metadata |
| `version` | Pack version |

## YAML format

```yaml
id: cisco-sip-ua-disabled
title: SIP-UA disabled operational guidance
description: Guidance when SIP-UA is administratively disabled.
vendor: cisco
platform: CUBE
category: operations
severity: critical
supported_object_types:
  - sip_ua
conditions:
  enabled: false
recommendations:
  - Enable SIP-UA and verify SIP registration.
  - Review voice service voip configuration.
references:
  - https://example.com/cube/sip-ua
metadata:
  source: cisco-vkf
version: "1.0"
```

## Matching rules

1. Object type must be listed in `supported_object_types`
2. Pack `vendor` / `platform` must match the object or be wildcard (`*`)
3. Every `conditions` entry must match object fields or metadata exactly
4. Empty `conditions` matches all objects of the supported type within scope

## Engine API

```python
from knowledge import KnowledgeEngine, KnowledgeLoader

loader = KnowledgeLoader()
loader.load_directory(packs_root)
engine = KnowledgeEngine(registry=loader.registry)

object_matches = engine.evaluate_object(sip_ua)
topology_report = engine.evaluate_topology(topology)
case_report = engine.evaluate_case(case)
```

## KnowledgeReport

| Field | Purpose |
|-------|---------|
| `matched_packs` | Ordered object-to-pack matches |
| `recommendations` | Deduplicated guidance |
| `references` | Deduplicated references |
| `summary` | Human-readable match summary |

## Future vendor packs

Vendor plugins can ship YAML packs under paths such as:

```
plugins/cisco/knowledge/
plugins/microsoft/knowledge/
```

A bootstrap step can load all packs into a shared `KnowledgeRegistry` without modifying core evaluation logic.

## Rule lifecycle

1. Author YAML pack
2. Validate with `KnowledgeLoader.load_file()`
3. Register in `KnowledgeRegistry`
4. Match during investigation via `KnowledgeEngine`
5. Surface recommendations in future report/CLI integrations

## Testing

```bash
pytest tests/test_knowledge_framework.py
```

## Related

- [VKF package README](../../core/knowledge/README.md)
- [Health framework v1](../sprint-6/health-framework-v1.md)
- [CVOM v1](../sprint-4/canonical-voice-object-model.md)
