# Genesys Cloud CX Professional Knowledge Pack v1

## Purpose

Sprint 14.1 delivers production-quality Genesys Cloud CX engineering assets built through the Engineering Asset Factory (EAF²). All assets pass factory validation and achieve quality scores of **100/100**.

This sprint creates deterministic taxonomy content only. It does not include Genesys Cloud connectivity, OAuth, REST API, GraphQL, or live configuration changes.

## Architecture

```text
Vendor Asset SDK
        │
        ▼
Engineering Asset Factory
        │
        ▼
Genesys Cloud CX Assets
        │
        ▼
Engineering Knowledge Framework
        │
        ▼
Future Genesys Cloud Investigation Engine
```

## Asset Inventory

| Type | Count | ID Range |
|------|-------|----------|
| Incidents | 25 | `VP-GENESYS-CLOUD-000001` – `VP-GENESYS-CLOUD-000025` |
| Runbooks | 10 | `VP-GENESYS-CLOUD-RB-001` – `VP-GENESYS-CLOUD-RB-010` |
| Verification Guides | 10 | `VP-GENESYS-CLOUD-VG-001` – `VP-GENESYS-CLOUD-VG-010` |
| References | 5 | `VP-GENESYS-CLOUD-REF-001` – `VP-GENESYS-CLOUD-REF-005` |
| **Total** | **50** | |

## Incident Categories

| Category | Incidents |
|----------|-----------|
| Authentication failure | 000001 |
| OAuth failure | 000002 |
| Token expired | 000003 |
| Organization unavailable | 000004 |
| Edge offline | 000005 |
| Trunk unavailable | 000006 |
| Carrier unavailable | 000007 |
| SIP OPTIONS failed | 000008 |
| TLS certificate expired | 000009 |
| Queue unavailable | 000010 |
| Queue member unavailable | 000011 |
| Agent not logged in | 000012 |
| Agent stuck interacting | 000013 |
| Call flow failure | 000014 |
| Architect publish issue | 000015 |
| Data Action failure | 000016 |
| Recording failure | 000017 |
| Conversation service unavailable | 000018 |
| Analytics unavailable | 000019 |
| WebRTC failure | 000020 |
| Media service unavailable | 000021 |
| Outbound campaign failure | 000022 |
| Presence synchronization issue | 000023 |
| BYOC Cloud trunk failure | 000024 |
| BYOC Premises Edge unavailable | 000025 |

## Runbooks

| ID | Name |
|----|------|
| RB-001 | Validate Authentication and OAuth |
| RB-002 | Validate Organization and Edge |
| RB-003 | Validate SIP Trunk and Carrier |
| RB-004 | Validate TLS and Security |
| RB-005 | Validate Queue and Routing |
| RB-006 | Validate Agent and Presence |
| RB-007 | Validate Architect and Call Flow |
| RB-008 | Validate Media and WebRTC |
| RB-009 | Validate Recording and Conversation |
| RB-010 | Validate BYOC and Campaign |

## Verification Guides

| ID | Name |
|----|------|
| VG-001 | Verify authentication and OAuth |
| VG-002 | Verify organization and Edge health |
| VG-003 | Verify trunk and carrier connectivity |
| VG-004 | Verify TLS and certificate health |
| VG-005 | Verify queue and routing |
| VG-006 | Verify agent and presence state |
| VG-007 | Verify Architect and call flow |
| VG-008 | Verify media and WebRTC path |
| VG-009 | Verify recording and conversation service |
| VG-010 | Verify BYOC and outbound campaign |

## References

| ID | Name |
|----|------|
| REF-001 | Genesys Cloud Architecture |
| REF-002 | OAuth and Authentication Reference |
| REF-003 | Edge and BYOC Reference |
| REF-004 | Architect and Routing Reference |
| REF-005 | Media and WebRTC Reference |

## Quality Gate

Every asset includes:

- title, description, severity
- symptoms, expected_findings
- known_causes, known_resolution
- rollback_steps, verification_steps
- related_asset_ids, references

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

## Constraints

- Read-only engineering content
- No API, OAuth, REST, GraphQL, or live connectivity
- No investigation engine, parsers, or health rules in this sprint
- Knowledge only

## Related Tests

- `tests/test_genesys_knowledge_library.py`

## Generator

- `scripts/generate_genesys_cloud_pack.py`
