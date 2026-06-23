# AudioCodes SBC Professional Knowledge Pack v1

## Purpose

Sprint 13.1 delivers production-quality AudioCodes SBC engineering assets built through the Engineering Asset Factory (EAF²). All assets pass factory validation and achieve quality scores of **100/100**.

This sprint creates deterministic taxonomy content only. It does not include AudioCodes connectivity, SSH, REST API access, or live configuration changes.

## Architecture

```text
Vendor Asset SDK
        │
        ▼
Engineering Asset Factory
        │
        ▼
AudioCodes SBC Assets
        │
        ▼
Engineering Knowledge Framework
        │
        ▼
Future AudioCodes Investigation Engine
```

## Asset Inventory

| Type | Count | ID Range |
|------|-------|----------|
| Incidents | 25 | `VP-AUDIOCODES-SBC-000001` – `VP-AUDIOCODES-SBC-000025` |
| Runbooks | 10 | `VP-AUDIOCODES-SBC-RB-001` – `VP-AUDIOCODES-SBC-RB-010` |
| Verification Guides | 10 | `VP-AUDIOCODES-SBC-VG-001` – `VP-AUDIOCODES-SBC-VG-010` |
| References | 5 | `VP-AUDIOCODES-SBC-REF-001` – `VP-AUDIOCODES-SBC-REF-005` |
| **Total** | **50** | |

## Incident Categories

| Category | Incidents |
|----------|-----------|
| SIP OPTIONS failure | 000001 |
| Provider 503 | 000002 |
| TLS certificate expired | 000003 |
| TLS negotiation failure | 000004 |
| SIP Interface down | 000005 |
| Proxy Set unavailable | 000006 |
| IP Group disabled | 000007 |
| IP Group mismatch | 000008 |
| Routing table issue | 000009 |
| Manipulation Set failure | 000010 |
| Media Realm failure | 000011 |
| RTP one-way audio | 000012 |
| SRTP mismatch | 000013 |
| Session license exhausted | 000014 |
| HA failover | 000015 |
| Standby synchronization failure | 000016 |
| SIP flood protection | 000017 |
| DoS protection | 000018 |
| 488 codec mismatch | 000019 |
| 403 forbidden | 000020 |
| 408 timeout | 000021 |
| SBC overload | 000022 |
| DNS resolution failure | 000023 |
| Gateway unreachable | 000024 |
| Registration failure | 000025 |

## Example Incidents

- SIP OPTIONS failure (`VP-AUDIOCODES-SBC-000001`)
- Provider 503 (`VP-AUDIOCODES-SBC-000002`)
- TLS certificate expired (`VP-AUDIOCODES-SBC-000003`)
- RTP one-way audio (`VP-AUDIOCODES-SBC-000012`)
- HA failover (`VP-AUDIOCODES-SBC-000015`)
- Registration failure (`VP-AUDIOCODES-SBC-000025`)

## Runbooks

| ID | Name |
|----|------|
| RB-001 | Validate SIP Trunk |
| RB-002 | Validate TLS Configuration |
| RB-003 | Validate Proxy Set and IP Group |
| RB-004 | Validate Routing and Manipulation |
| RB-005 | Validate Media and Codecs |
| RB-006 | Validate HA Cluster |
| RB-007 | Validate Security Policies |
| RB-008 | Validate Provider Connectivity |
| RB-009 | Validate Session Licensing |
| RB-010 | Validate DNS and Capacity |

## Verification Guides

| ID | Name |
|----|------|
| VG-001 | Verify SIP trunk health |
| VG-002 | Verify TLS and SRTP |
| VG-003 | Verify Proxy Set and IP Group |
| VG-004 | Verify routing table |
| VG-005 | Verify media path |
| VG-006 | Verify HA synchronization |
| VG-007 | Verify security policies |
| VG-008 | Verify provider gateway |
| VG-009 | Verify session licensing |
| VG-010 | Verify DNS and capacity |

## References

| ID | Title |
|----|-------|
| REF-001 | AudioCodes SBC Architecture |
| REF-002 | SIP Trunk Configuration Reference |
| REF-003 | TLS Certificate Management |
| REF-004 | Media Realm Reference |
| REF-005 | HA Cluster Reference |

## Relationships

Each incident links to:

- One or more runbooks (`VP-AUDIOCODES-SBC-RB-*`)
- One or more verification guides (`VP-AUDIOCODES-SBC-VG-*`)
- One or more references (`VP-AUDIOCODES-SBC-REF-*`)

All incidents include symptoms, expected findings, likely causes, known resolution, rollback steps, verification steps, and related asset IDs.

## Quality Statistics

All 50 AudioCodes SBC professional pack assets:

- Pass `EngineeringAssetFactory.validate_assets()`
- Score **100/100** on deterministic quality criteria
- Include required incident metadata: symptoms, findings, causes, resolution, rollback, verification

Validate locally:

```bash
voicepilot assets validate
voicepilot assets quality
voicepilot assets stats
voicepilot assets search AudioCodes
voicepilot assets search "TLS certificate"
voicepilot assets show VP-AUDIOCODES-SBC-000001
```

## Location

```text
knowledge/incidents/audiocodes/sbc/
knowledge/runbooks/audiocodes/sbc/
knowledge/verification/audiocodes/sbc/
knowledge/references/audiocodes/sbc/
```

## Generator

Assets are generated deterministically by:

```bash
python scripts/generate_audiocodes_sbc_pack.py
```

## Related Tests

- [`../../tests/test_audiocodes_knowledge_library.py`](../../tests/test_audiocodes_knowledge_library.py)

## Related Documentation

- [`../../architecture/part-4-platform/12-audiocodes-knowledge-library.md`](../../architecture/part-4-platform/12-audiocodes-knowledge-library.md)
- [`../sprint-11/engineering-asset-factory-v1.md`](../sprint-11/engineering-asset-factory-v1.md)
- [`../sprint-11/vendor-asset-sdk-v1.md`](../sprint-11/vendor-asset-sdk-v1.md)
