# 12 — AudioCodes SBC Knowledge Library

> **Status:** Implemented

## Purpose

Document the AudioCodes SBC Professional Knowledge Pack: 50 deterministic engineering assets for AudioCodes Mediant SBC deployments that pass EAF² validation and load through the Engineering Knowledge Framework.

This sprint delivers read-only engineering content only. No investigation engine, AudioCodes connectivity, SSH, REST API, or live configuration changes are included.

## Repository Modules Involved

- Knowledge assets: [`../../knowledge/incidents/audiocodes/sbc/`](../../knowledge/incidents/audiocodes/sbc/)
- Loader: [`../../core/engineering_knowledge/knowledge_library_loader.py`](../../core/engineering_knowledge/knowledge_library_loader.py)
- Asset models: [`../../core/engineering_assets/`](../../core/engineering_assets/)
- Factory validation: [`../../core/asset_factory/`](../../core/asset_factory/)
- Vendor scaffolding: [`../../core/vendor_sdk/`](../../core/vendor_sdk/)
- Generator: [`../../scripts/generate_audiocodes_sbc_pack.py`](../../scripts/generate_audiocodes_sbc_pack.py)

## Pipeline

```text
Vendor Asset SDK → Engineering Asset Factory → AudioCodes SBC Assets → Engineering Knowledge Framework → Future AudioCodes Investigation Engine
```

## Asset Inventory

| Type | Count | ID Pattern |
|------|-------|------------|
| Incidents | 25 | `VP-AUDIOCODES-SBC-000001` – `000025` |
| Runbooks | 10 | `VP-AUDIOCODES-SBC-RB-001` – `RB-010` |
| Verification Guides | 10 | `VP-AUDIOCODES-SBC-VG-001` – `VG-010` |
| References | 5 | `VP-AUDIOCODES-SBC-REF-001` – `REF-005` |

## Quality Gate

All assets pass EAF² validation with quality score **100/100**.

## CLI

```bash
voicepilot assets search AudioCodes
voicepilot assets search "TLS certificate"
voicepilot assets show VP-AUDIOCODES-SBC-000001
voicepilot assets stats
voicepilot assets quality
voicepilot assets validate
```

## Related Tests

- [`../../tests/test_audiocodes_knowledge_library.py`](../../tests/test_audiocodes_knowledge_library.py)

## Related Documentation

- [`../../docs/sprint-13/audiocodes-professional-pack-v1.md`](../../docs/sprint-13/audiocodes-professional-pack-v1.md)
- [08 — Engineering Asset Factory](../part-3-engines/08-engineering-asset-factory.md)
- [10 — Vendor Asset SDK](../part-3-engines/10-vendor-asset-sdk.md)

## Cross References

- [04 — Knowledge Packs](04-knowledge-packs.md)
- [07 — Microsoft Teams Knowledge Library](07-microsoft-teams-knowledge-library.md)
