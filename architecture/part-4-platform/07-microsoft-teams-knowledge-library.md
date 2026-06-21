# 07 — Microsoft Teams Knowledge Library

> **Status:** Implemented

## Purpose

Document the Microsoft Teams Professional Knowledge Pack: 50 deterministic engineering assets for Microsoft Teams Phone that pass EAF² validation and load through the Engineering Knowledge Framework.

This sprint delivers read-only engineering content only. No investigation engine, Microsoft Graph, PowerShell, or live tenant connectivity is included.

## Repository Modules Involved

- Knowledge assets: [`../../knowledge/incidents/microsoft/teams-phone/`](../../knowledge/incidents/microsoft/teams-phone/)
- Loader: [`../../core/engineering_knowledge/knowledge_library_loader.py`](../../core/engineering_knowledge/knowledge_library_loader.py)
- Asset models: [`../../core/engineering_assets/`](../../core/engineering_assets/)
- Factory validation: [`../../core/asset_factory/`](../../core/asset_factory/)
- Vendor scaffolding: [`../../core/vendor_sdk/`](../../core/vendor_sdk/)

## Pipeline

```text
Vendor Asset SDK → Engineering Asset Factory → Microsoft Teams Assets → Engineering Knowledge Framework → Future Teams Investigation Engine
```

## Asset Inventory

| Type | Count | ID Pattern |
|------|-------|------------|
| Incidents | 25 | `VP-MS-TEAMS-000001` – `000025` |
| Runbooks | 10 | `VP-MS-TEAMS-RB-001` – `RB-010` |
| Verification Guides | 10 | `VP-MS-TEAMS-VG-001` – `VG-010` |
| References | 5 | `VP-MS-TEAMS-REF-001` – `REF-005` |

## Quality Gate

All assets pass EAF² validation with quality score **≥ 95**.

## CLI

```bash
voicepilot assets search Teams
voicepilot assets search "Direct Routing"
voicepilot assets show VP-MS-TEAMS-000001
voicepilot assets stats
voicepilot assets quality
voicepilot assets validate
```

## Related Tests

- [`../../tests/test_microsoft_teams_knowledge_library.py`](../../tests/test_microsoft_teams_knowledge_library.py)

## Related Documentation

- [`../../docs/sprint-11/microsoft-teams-professional-pack-v1.md`](../../docs/sprint-11/microsoft-teams-professional-pack-v1.md)
- [08 — Engineering Asset Factory](../part-3-engines/08-engineering-asset-factory.md)
- [10 — Vendor Asset SDK](../part-3-engines/10-vendor-asset-sdk.md)

## Cross References

- [04 — Knowledge Packs](04-knowledge-packs.md)
- [06 — CUCM Investigation Pipeline](06-cucm-investigation-pipeline.md)
