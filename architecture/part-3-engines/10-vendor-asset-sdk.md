# 10 — Vendor Asset SDK

> **Status:** Implemented

## Purpose

Document the Vendor Asset SDK: a vendor-neutral scaffolding engine that generates deterministic engineering assets and validates them through EAF² before they enter the knowledge library.

The SDK never performs investigations. It only creates editable engineering content.

## Repository Modules Involved

- [`../../core/vendor_sdk/vendor_sdk.py`](../../core/vendor_sdk/vendor_sdk.py) — `VendorAssetSdk` engine
- [`../../core/vendor_sdk/vendor_catalog.py`](../../core/vendor_sdk/vendor_catalog.py) — pre-registered vendors and products
- [`../../core/vendor_sdk/asset_templates.py`](../../core/vendor_sdk/asset_templates.py) — six asset type templates
- [`../../core/vendor_sdk/vendor_models.py`](../../core/vendor_sdk/vendor_models.py) — immutable dataclasses
- [`../../core/vendor_sdk/id_generator.py`](../../core/vendor_sdk/id_generator.py) — deterministic asset IDs
- [`../../core/vendor_sdk/yaml_writer.py`](../../core/vendor_sdk/yaml_writer.py) — YAML output
- [`../../core/vendor_sdk/markdown_writer.py`](../../core/vendor_sdk/markdown_writer.py) — README and markdown docs
- Factory integration: [`../../core/asset_factory/`](../../core/asset_factory/)

## Pipeline

```text
Vendor → Product → Template → VendorAssetSdk → EngineeringAssetFactory → Engineering Assets
```

## Responsibilities

| Component | Role |
|-----------|------|
| `VendorDefinition` | Registered vendor metadata |
| `ProductDefinition` | Product under a vendor |
| `AssetTemplate` | Required fields per asset type |
| `AssetBlueprint` | Package IDs and cross-references |
| `VendorAssetSdk` | Register vendors/products, generate assets, validate quality |

## Pre-Registered Catalog

Seven vendors and eighteen products are bundled. No Cisco-, Microsoft-, or AudioCodes-specific investigation logic is included.

## Generation Methods

- `generate_incident`
- `generate_runbook`
- `generate_verification`
- `generate_reference`
- `generate_best_practice`
- `generate_bug_reference`
- `generate_package` — full six-asset incident package
- `generate_markdown_documentation`

## Quality Gate

All generated assets must pass EAF² validation with quality score **≥ 95**.

## CLI

```bash
voicepilot sdk vendors
voicepilot sdk products [--vendor Cisco]
voicepilot sdk generate incident|runbook|verification|reference|best-practice|bug|package \
  --vendor Cisco --product CUCM --title "Phone Registration Failure" [--output dir]
```

## Related Tests

- [`../../tests/test_vendor_sdk.py`](../../tests/test_vendor_sdk.py)

## Related Documentation

- [`../../docs/sprint-11/vendor-asset-sdk-v1.md`](../../docs/sprint-11/vendor-asset-sdk-v1.md)
- [08 — Engineering Asset Factory](08-engineering-asset-factory.md)

## Cross References

- [05 — Knowledge Framework](05-knowledge-framework.md)
- [Part 4 — Knowledge Packs](../part-4-platform/04-knowledge-packs.md)
