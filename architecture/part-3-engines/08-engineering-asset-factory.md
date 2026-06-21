# 08 — Engineering Asset Factory

> **Status:** Implemented

## Purpose

Document the Engineering Asset Factory (EAF²): the knowledge production pipeline that converts structured engineering content into validated `EngineeringAsset` instances.

EAF² is separate from the Engineering Asset Framework (EAF) in `core/engineering_assets/`, which defines models, loading, and search.

## Repository Modules Involved

- [`../../core/asset_factory/asset_factory.py`](../../core/asset_factory/asset_factory.py) — pipeline orchestrator
- [`../../core/asset_factory/asset_validator.py`](../../core/asset_factory/asset_validator.py) — validation rules
- [`../../core/asset_factory/asset_builder.py`](../../core/asset_factory/asset_builder.py) — normalization and templates
- [`../../core/asset_factory/asset_quality.py`](../../core/asset_factory/asset_quality.py) — quality scoring
- [`../../core/asset_factory/asset_statistics.py`](../../core/asset_factory/asset_statistics.py) — collection statistics
- [`../../core/asset_factory/asset_relationship_builder.py`](../../core/asset_factory/asset_relationship_builder.py) — relationship generation
- Asset models: [`../../core/engineering_assets/`](../../core/engineering_assets/)

## Knowledge Production Pipeline

```text
Raw Structured Data → Validation → Normalization → Relationships → Quality → Statistics → EngineeringAsset
```

## Quality Validation Pipeline

| Check | Description |
|-------|-------------|
| Required metadata | asset_id, title, vendor, product, version, category, status, severity |
| Unique IDs | No duplicate asset IDs in batch |
| Duplicate titles | Detected across batch |
| Related assets | Referenced IDs must exist |
| Quality score | 0–100 deterministic criteria |

## CLI

```bash
voicepilot assets validate
voicepilot assets stats
voicepilot assets quality
voicepilot assets relationships
```

## Related Tests

- [`../../tests/test_asset_factory.py`](../../tests/test_asset_factory.py)
- [`../../tests/test_engineering_assets.py`](../../tests/test_engineering_assets.py)

## Related Documentation

- [`../../docs/sprint-11/engineering-asset-factory-v1.md`](../../docs/sprint-11/engineering-asset-factory-v1.md)
- [`../../docs/sprint-10/engineering-asset-framework-v1.md`](../../docs/sprint-10/engineering-asset-framework-v1.md)

## Cross References

- [05 — Knowledge Framework](05-knowledge-framework.md)
- [Part 4 — Knowledge Packs](../part-4-platform/04-knowledge-packs.md)
