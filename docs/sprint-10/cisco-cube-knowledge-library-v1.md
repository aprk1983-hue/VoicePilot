# Cisco CUBE Knowledge Library v1

## Purpose

Sprint 10.4 adds the first production-quality Cisco CUBE engineering knowledge library on top of the Engineering Asset Framework (EAF) and Engineering Knowledge Framework (EKF).

Knowledge lives as YAML assets under `knowledge/`. EAF loads assets; EKF derives explainable knowledge entries and relationships without embedding Cisco logic in the core frameworks.

## Asset Matrix

| Type | Count | Location |
|------|-------|----------|
| Incidents | 10 | `knowledge/incidents/cisco/cube/` |
| Verification Guides | 5 | `knowledge/verification/cisco/cube/` |
| Runbooks | 5 | `knowledge/runbooks/cisco/cube/` |
| References | 5 | `knowledge/references/cisco/cube/` |

Existing VKF packs under `knowledge/packs/` are unchanged.

## Incident List

| Asset ID | Incident |
|----------|----------|
| VP-CISCO-CUBE-000001 | SIP-UA disabled |
| VP-CISCO-CUBE-000002 | Missing outbound dial peer |
| VP-CISCO-CUBE-000003 | Provider 503 |
| VP-CISCO-CUBE-000004 | Codec mismatch 488 |
| VP-CISCO-CUBE-000005 | Dial peer shutdown/out of service |
| VP-CISCO-CUBE-000006 | SIP OPTIONS failure |
| VP-CISCO-CUBE-000007 | TLS certificate expired |
| VP-CISCO-CUBE-000008 | Translation rule mismatch |
| VP-CISCO-CUBE-000009 | SIP profile header issue |
| VP-CISCO-CUBE-000010 | One-way audio / RTP path issue |

## Relationship Model

Each incident YAML includes `related_asset_ids` linking to:

- runbooks (`VP-CISCO-CUBE-RB-*`)
- verification guides (`VP-CISCO-CUBE-VG-*`)
- references (`VP-CISCO-CUBE-REF-*`)

Bootstrap derives EKF `KnowledgeRelationship` entries with type `REFERENCES` from those links.

Matching uses `expected_findings` mapped to EKF `match_signals`, enabling deterministic case matching for VP-CUBE-0001 scenarios such as:

- `sip_ua_disabled`
- `provider_503`
- `missing_outbound_dial_peer`
- `codec_mismatch_488`
- `dial_peer_shutdown`

## Loader Integration

- `EngineeringAssetLoader` merges incident extension fields into asset metadata
- `load_engineering_knowledge_library()` loads incidents/runbooks/verification/references YAML
- `default_engineering_knowledge_engine()` returns a cached EKF engine backed by the library

Bootstrap module: `core/engineering_knowledge/engineering_knowledge_bootstrap.py`

## CLI

```bash
voicepilot assets search "sip-ua"
voicepilot assets show VP-CISCO-CUBE-000001
voicepilot assets stats
```

The `assets` namespace avoids conflict with the existing VKF `knowledge` health evaluation path.

## Search Examples

```bash
voicepilot assets search "503"
voicepilot assets search "dial peer"
voicepilot assets show VP-CISCO-CUBE-000003
```

## Current Limitations

- In-memory only; assets reload on process start
- Incidents 6–10 are library-ready but not all have full VP-CUBE scenario coverage yet
- No REST API or persistence layer
- No AI retrieval

## Future Expansion

This library is structured to scale to 100+ Cisco CUBE incidents by adding YAML assets and relationships only. Future work:

- Additional incident packs by category (TLS, media, provider, dial-plan)
- Deeper linkage to discovery and health rule IDs
- REST/SDK exposure through the VoicePilot service layer
- Optional AI ranking above deterministic EKF matches
