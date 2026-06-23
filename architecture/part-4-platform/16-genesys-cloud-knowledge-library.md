# 16 — Genesys Cloud CX Knowledge Library

> **Status:** Implemented

## Purpose

Document the Genesys Cloud CX Professional Knowledge Pack: 50 deterministic engineering assets for Genesys Cloud CX deployments that pass EAF² validation and load through the Engineering Knowledge Framework.

This sprint delivers read-only engineering content only. No investigation engine, Genesys Cloud connectivity, OAuth, REST API, GraphQL, or live configuration changes are included.

## Repository Modules Involved

- Knowledge assets: [`../../knowledge/incidents/genesys/cloud/`](../../knowledge/incidents/genesys/cloud/)
- Loader: [`../../core/engineering_knowledge/knowledge_library_loader.py`](../../core/engineering_knowledge/knowledge_library_loader.py)
- Asset models: [`../../core/engineering_assets/`](../../core/engineering_assets/)
- Factory validation: [`../../core/asset_factory/`](../../core/asset_factory/)
- Vendor scaffolding: [`../../core/vendor_sdk/`](../../core/vendor_sdk/)
- Generator: [`../../scripts/generate_genesys_cloud_pack.py`](../../scripts/generate_genesys_cloud_pack.py)

## Pipeline

```text
Vendor Asset SDK → Engineering Asset Factory → Genesys Cloud CX Assets → Engineering Knowledge Framework → Future Genesys Cloud Investigation Engine
```

## Asset Inventory

| Type | Count | ID Pattern |
|------|-------|------------|
| Incidents | 25 | `VP-GENESYS-CLOUD-000001` – `000025` |
| Runbooks | 10 | `VP-GENESYS-CLOUD-RB-001` – `RB-010` |
| Verification Guides | 10 | `VP-GENESYS-CLOUD-VG-001` – `VG-010` |
| References | 5 | `VP-GENESYS-CLOUD-REF-001` – `REF-005` |

## Quality Gate

All assets pass EAF² validation with quality score **100/100**.

## CLI

```bash
voicepilot assets search Genesys
voicepilot assets search "OAuth failure"
voicepilot assets show VP-GENESYS-CLOUD-000001
voicepilot assets stats
voicepilot assets quality
voicepilot assets validate
```

## Related Tests

- [`../../tests/test_genesys_knowledge_library.py`](../../tests/test_genesys_knowledge_library.py)

## Related Documentation

- [`../../docs/sprint-14/genesys-professional-pack-v1.md`](../../docs/sprint-14/genesys-professional-pack-v1.md)
- [08 — Engineering Asset Factory](../part-3-engines/08-engineering-asset-factory.md)
- [10 — Vendor Asset SDK](../part-3-engines/10-vendor-asset-sdk.md)

## Cross References

- [04 — Knowledge Packs](04-knowledge-packs.md)
- [12 — AudioCodes SBC Knowledge Library](12-audiocodes-knowledge-library.md)
