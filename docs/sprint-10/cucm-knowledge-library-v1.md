# Cisco CUCM Knowledge Library v1

## Purpose

Sprint 10.5 adds the first production-quality Cisco Unified Communications Manager (CUCM) engineering knowledge library on top of the Engineering Asset Framework (EAF) and Engineering Knowledge Framework (EKF).

Knowledge lives as YAML assets under `knowledge/`. The existing `load_engineering_knowledge_library()` loader discovers CUCM assets automatically alongside CUBE assets. No Cisco-specific logic is embedded in EAF or EKF.

## Asset Matrix

| Type | Count | Location |
|------|-------|----------|
| Incidents | 25 | `knowledge/incidents/cisco/cucm/` |
| Verification Guides | 10 | `knowledge/verification/cisco/cucm/` |
| Runbooks | 10 | `knowledge/runbooks/cisco/cucm/` |
| References | 10 | `knowledge/references/cisco/cucm/` |

Combined library totals (CUBE + CUCM): 80 engineering assets.

## Incident Categories

| Category | Count | Asset IDs |
|----------|-------|-----------|
| Phone Registration | 5 | VP-CISCO-CUCM-000001 – 000005 |
| SIP Trunks | 5 | VP-CISCO-CUCM-000006 – 000010 |
| Call Routing | 5 | VP-CISCO-CUCM-000011 – 000015 |
| Media Resources | 5 | VP-CISCO-CUCM-000016 – 000020 |
| Cluster Health | 5 | VP-CISCO-CUCM-000021 – 000025 |

## Incident List

| Asset ID | Incident |
|----------|----------|
| VP-CISCO-CUCM-000001 | Phone not registering — TFTP unreachable |
| VP-CISCO-CUCM-000002 | Phone registration rejected — authentication failure |
| VP-CISCO-CUCM-000003 | Phone stuck initializing — CM group mismatch |
| VP-CISCO-CUCM-000004 | Bulk phone deregistration after publisher failover |
| VP-CISCO-CUCM-000005 | Phone registration blocked by firewall |
| VP-CISCO-CUCM-000006 | SIP trunk down — TCP connection timeout |
| VP-CISCO-CUCM-000007 | SIP trunk TLS handshake failure |
| VP-CISCO-CUCM-000008 | SIP trunk OPTIONS keepalive failure |
| VP-CISCO-CUCM-000009 | SIP trunk DTMF mismatch |
| VP-CISCO-CUCM-000010 | SIP trunk authentication failure |
| VP-CISCO-CUCM-000011 | Route pattern misconfiguration — call blocked |
| VP-CISCO-CUCM-000012 | Translation pattern strips leading digits |
| VP-CISCO-CUCM-000013 | CSS restriction blocks external route |
| VP-CISCO-CUCM-000014 | Hunt group no answer — forwarding misconfiguration |
| VP-CISCO-CUCM-000015 | Time-of-day routing denies after-hours call |
| VP-CISCO-CUCM-000016 | Conference bridge unavailable — MTP exhaustion |
| VP-CISCO-CUCM-000017 | MOH server unreachable |
| VP-CISCO-CUCM-000018 | Transcoder allocation failure |
| VP-CISCO-CUCM-000019 | Annunciator failure — no tones |
| VP-CISCO-CUCM-000020 | MOH codec mismatch causing silence |
| VP-CISCO-CUCM-000021 | Publisher database replication broken |
| VP-CISCO-CUCM-000022 | Subscriber split-brain — NTP skew |
| VP-CISCO-CUCM-000023 | License count exceeded — node service impact |
| VP-CISCO-CUCM-000024 | Critical service down — Cisco DB |
| VP-CISCO-CUCM-000025 | Certificate management service failure — Tomcat |

## Relationship Model

Each incident YAML includes `related_asset_ids` linking to:

- runbooks (`VP-CISCO-CUCM-RB-*`)
- verification guides (`VP-CISCO-CUCM-VG-*`)
- references (`VP-CISCO-CUCM-REF-*`)

Bootstrap derives EKF `KnowledgeRelationship` entries with type `REFERENCES` from those links.

Matching uses `expected_findings` mapped to EKF `match_signals` for deterministic finding-based case matching.

## Loader Integration

- `iter_library_yaml_paths()` recursively loads all YAML under `knowledge/incidents`, `runbooks`, `verification`, and `references`
- `default_engineering_knowledge_engine()` returns a cached EKF engine backed by the combined library
- Existing VKF packs under `knowledge/packs/` are unchanged

Bootstrap module: `core/engineering_knowledge/engineering_knowledge_bootstrap.py`

## CLI

Existing `assets` commands automatically include CUCM assets:

```bash
voicepilot assets search "phone registration"
voicepilot assets search "sip trunk"
voicepilot assets show VP-CISCO-CUCM-000001
voicepilot assets stats
```

## Search Examples

```bash
voicepilot assets search "replication"
voicepilot assets search "hunt group"
voicepilot assets show VP-CISCO-CUCM-000021
```

## Current Limitations

- Knowledge-only assets; no automated CUCM CLI collection or parsers
- EKF matching is signal-based via `expected_findings`; no VP-CUCM scenario pack yet
- Support assets are shared across related incidents within each category group
- No cross-vendor (Teams, Expressway) knowledge in this sprint

## Future Expansion

Scale to 100+ Cisco CUCM incidents by:

1. Adding YAML files under the same directory structure
2. Extending `expected_findings` to align with health rules and scenario outputs
3. Introducing VP-CUCM scenario packs for end-to-end EKF validation
4. Splitting category-specific reference assets as incident count grows
