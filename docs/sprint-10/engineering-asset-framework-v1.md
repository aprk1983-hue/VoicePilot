# Engineering Asset Framework v1

## Purpose

VoicePilot will eventually curate a broad engineering knowledge base: incidents, runbooks, verification guides, vendor bugs, TAC resolutions, lab validations, scripts, videos, and reference documents.

The Engineering Asset Framework (EAF) provides the reusable foundation for that content without embedding vendor-specific logic in the core platform.

Sprint 10.2 delivers the framework only. Content libraries such as Cisco incidents or the Engineering Knowledge Framework (EKF) are future layers built on top of EAF.

## Architecture

```text
Future Content Libraries (Cisco, Microsoft, AudioCodes, Genesys, ...)
                        │
                        ▼
            Engineering Asset Framework (EAF)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Asset Models    Registry/Search   Loader/Report
```

Core components:

| Module | Responsibility |
|--------|----------------|
| `asset_models.py` | Immutable `EngineeringAsset` and `EngineeringRelationship` |
| `asset_types.py` | Vendor-neutral `EngineeringAssetType` enum |
| `asset_categories.py` | Vendor-neutral `EngineeringCategory` enum |
| `asset_registry.py` | In-memory asset registry with deterministic queries |
| `asset_relationships.py` | Typed relationship registry |
| `asset_loader.py` | YAML loading and validation |
| `asset_search.py` | Deterministic text and field filtering |
| `asset_report.py` | Markdown collection summaries |

## Why EAF Exists

- **One canonical asset model** for all engineering knowledge
- **Vendor-neutral core** so Cisco/Microsoft/AudioCodes/Genesys content stays in libraries
- **Relationship graph primitives** for future knowledge navigation
- **Deterministic search** without AI embeddings in v1
- **Stable import surface** for CLI, REST, SDK, and future assistants

## Relationship to EKF

EAF defines how assets are modeled, registered, linked, searched, and reported.

EKF (future) will compose curated engineering knowledge packs on top of EAF — similar to how playbook plugins compose on the runtime kernel without moving vendor logic into core engines.

EAF must remain generic. EKF adds curated content and domain packaging.

## What EAF Does Not Do (v1)

- No AI or semantic retrieval
- No FastAPI or REST endpoints
- No database or filesystem persistence
- No Cisco/Microsoft/AudioCodes/Genesys-specific code
- No incident libraries yet

## Public Models

### `EngineeringAsset`

Immutable asset with:

- identity: `asset_id`, `title`, `asset_type`, `category`
- scope: `vendor`, `product`, `version`
- content: `summary`, `description`, `tags`, `references`
- graph: `related_asset_ids`
- provenance: `metadata`, `source`, `confidence`, `status`, timestamps

### `EngineeringRelationship`

Typed edge between two assets using `EngineeringRelationshipType`:

- `RELATED_TO`, `REFERENCES`, `SUPERSEDES`, `REQUIRES`, `VERIFIES`
- `IMPLEMENTS`, `DOCUMENTS`, `KNOWN_ISSUE`, `FIXES`, `DUPLICATE_OF`

## Example Usage

```python
from engineering_assets import (
    EngineeringAsset,
    EngineeringAssetLoader,
    EngineeringAssetRegistry,
    EngineeringAssetSearch,
    EngineeringAssetReport,
    EngineeringAssetType,
    EngineeringCategory,
    EngineeringAssetStatus,
)

registry = EngineeringAssetRegistry()
loader = EngineeringAssetLoader()

asset = loader.load_file(path_to_yaml)
registry.register(asset)

results = registry.find_by_vendor("ExampleVendor")
search = EngineeringAssetSearch(registry)
matches = search.search_text("verification")

report = EngineeringAssetReport(registry)
print(report.to_markdown())
```

## Future Incident Libraries

Incident packs will register assets such as:

- `EngineeringAssetType.INCIDENT`
- `EngineeringAssetType.TAC_RESOLUTION`
- `EngineeringAssetType.BUG`

Each pack supplies YAML content and relationships. EAF stores and queries them generically.

## Future Knowledge Graph

`EngineeringRelationshipRegistry` enables graph queries such as:

- runbook `VERIFIES` configuration guide
- bug `FIXES` known issue
- article `REFERENCES` lab validation

Future graph traversal APIs can build on the relationship registry without changing asset models.

## Future AI Retrieval

When AI retrieval is added, it should sit above EAF:

1. Deterministic EAF search narrows candidate assets
2. Optional AI ranking summarizes or selects from filtered results

EAF remains the source of truth; AI must not replace deterministic asset identity or relationships.

## Current Limitations

- In-memory only; registries reset between processes
- Simple substring search; no ranking beyond deterministic filters
- YAML loader validates structure but does not enforce content schemas per asset type

## Package Location

- Implementation: `core/engineering_assets/`
- Import: `from engineering_assets import EngineeringAssetRegistry`
