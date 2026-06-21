# Engineering Asset Framework (EAF)

The `engineering_assets` package provides a vendor-neutral foundation for
engineering knowledge assets such as runbooks, verification guides, best
practices, lab validations, and future incident libraries.

## Principles

- Immutable domain models
- In-memory registry and search only
- No vendor-specific logic in the framework
- No AI, database, or persistence in v1

## Usage

```python
from engineering_assets import EngineeringAssetRegistry, EngineeringAsset

registry = EngineeringAssetRegistry()
registry.register(asset)
results = registry.find_by_vendor("ExampleVendor")
```

See [Engineering Asset Framework v1](../../docs/sprint-10/engineering-asset-framework-v1.md).
