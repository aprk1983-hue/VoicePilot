# Engineering Asset Factory (EAF²)

The **Engineering Asset Factory** converts raw structured engineering content into production-ready `EngineeringAsset` instances.

This is distinct from the **Engineering Asset Framework (EAF)** in `core/engineering_assets/`, which defines models, loading, and search. EAF² is the production pipeline that validates, normalizes, links, and scores assets before they enter a library.

## Pipeline

```text
Raw Structured Data
        ↓
   Validation
        ↓
  Normalization
        ↓
Relationship Generation
        ↓
Knowledge Placeholders
        ↓
  Quality Checks
        ↓
   Statistics
        ↓
Engineering Asset
```

## Usage

```python
from asset_factory import EngineeringAssetFactory

factory = EngineeringAssetFactory()
result = factory.build(raw_dict)
asset = result.asset
quality_score = result.quality.score
relationships = result.relationships
```

## Read-Only

EAF² does not persist assets, parse PDFs, or invoke AI. It operates on in-memory structured dictionaries only.
