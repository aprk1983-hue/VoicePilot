# Engineering Asset Factory v1

## Purpose

Sprint 11.1 introduces the **Engineering Asset Factory (EAF²)** — a deterministic pipeline that converts raw structured engineering content into production-ready `EngineeringAsset` instances.

EAF² is distinct from the **Engineering Asset Framework (EAF)** in `core/engineering_assets/`, which defines models, loading, and search. EAF² is the **knowledge production pipeline** used to validate and prepare assets before they enter a library.

VoicePilot remains read-only. EAF² does not parse PDFs, invoke AI, or persist data.

## Architecture

```text
Raw Structured Data (dict)
        │
        ▼
   AssetValidator ──► duplicate / required field checks
        │
        ▼
   AssetBuilder ──► templates + normalization
        │
        ▼
AssetRelationshipBuilder ──► Incident → Runbook → Verification → Reference → Best Practice → Bug
        │
        ▼
   AssetQualityScorer ──► 0–100 deterministic score
        │
        ▼
AssetStatisticsGenerator ──► vendor/product/category counts
        │
        ▼
   EngineeringAsset
```

## Pipeline Stages

| Stage | Module | Responsibility |
|-------|--------|----------------|
| Validation | `asset_validator.py` | Required fields, unique IDs, duplicate titles, related asset existence |
| Normalization | `asset_builder.py` | Template placeholders, metadata promotion |
| Relationships | `asset_relationship_builder.py` | Typed links from `related_asset_ids` and chain rules |
| Quality | `asset_quality.py` | 0–100 score across metadata, references, symptoms, findings, resolution |
| Statistics | `asset_statistics.py` | Vendor/product/category counts, average quality, duplicates |

## Quality Scoring Criteria

Each criterion contributes to a 0–100 score:

- Required metadata (15)
- Relationships (10)
- References (10)
- Verification steps (10)
- Runbook link (10)
- Rollback (5)
- Known symptoms (10)
- Known findings (10)
- Known causes (10)
- Known resolution (10)

## Factory Usage

```python
from asset_factory import EngineeringAssetFactory

factory = EngineeringAssetFactory()
result = factory.build(raw_dict)

asset = result.asset
quality = result.quality.score
relationships = result.relationships
```

Batch production:

```python
results = factory.build_batch([incident_dict, runbook_dict, verification_dict])
stats = factory.asset_statistics([r.asset for r in results])
```

## CLI

```bash
voicepilot assets validate
voicepilot assets stats
voicepilot assets quality
voicepilot assets relationships
```

## Runtime and Service

```python
report = runtime.validate_assets()
stats = runtime.asset_statistics()

service = VoicePilotService()
result = service.validate_assets()
stats = service.asset_statistics()
```

## Input Sources (Future)

Structured dictionaries may originate from:

- Cisco TAC notes
- Microsoft Learn articles
- AudioCodes manuals
- Genesys documentation
- Internal SOPs
- Previous incidents
- RFC references

PDF parsing and LLM extraction are out of scope for v1.

## Read-Only Limitations

- Operates on in-memory structured dictionaries only
- Does not write to filesystem or database
- Does not modify bundled library assets during validation
