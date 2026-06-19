# Canonical Voice Object Model (CVOM) v1

CVOM is VoicePilot's vendor-neutral representation of enterprise voice deployments. Parsers populate CVOM objects; engines consume them.

## Why CVOM exists

Today, parsers emit **findings** (signals like `sip_ua_disabled`). Findings are useful for correlation but do not capture the full structured state of a deployment.

CVOM provides:

- **One schema** for Cisco CUBE, Microsoft Teams, Ribbon, AudioCodes, Oracle SBC, and future platforms
- **Provenance** — every object records parser, command, and evidence ID
- **Immutability** — objects are never edited; new evidence creates new objects
- **Registry lookup** — engines query by ID, type, hostname, or parser

## Object catalog

| CVOM object | Typical parser source |
|-------------|----------------------|
| `Device` | `show version`, inventory |
| `Interface` | `show ip interface brief` |
| `VoiceService` | `show run \| sec voice service voip` |
| `SipUA` | `show sip-ua status` |
| `DialPeer` | `show dial-peer voice summary` |
| `CodecClass` | `show voice class codec` |
| `ServerGroup` | `show voice class server-group` |
| `TranslationRule` | `show translation-rule` |
| `TranslationProfile` | `show translation-profile` |
| `Provider` | SIP trunk / registrar config |

## Base object: `VoiceObject`

Every CVOM type extends `VoiceObject`:

| Field | Purpose |
|-------|---------|
| `id` | Unique ID (`VOBJ-…`) |
| `object_type` | Canonical type string |
| `vendor` / `platform` / `hostname` | Deployment context |
| `name` / `description` | Human labels |
| `source_parser` / `source_command` / `source_evidence_id` | Provenance |
| `confidence` | Parser confidence (0–100) |
| `metadata` | Extensible vendor fields |

## How parsers use CVOM (future)

```
show dial-peer voice summary
        ↓
CiscoShowDialPeerVoiceSummaryParser
        ↓
DialPeer objects (one per peer)
        ↓
ObjectRegistry.register()
```

Parsers will continue emitting findings during migration. CVOM objects become the structured system of record.

## How engines consume CVOM (future)

| Engine | Consumption |
|--------|-------------|
| Correlation | Read `SipUA.enabled` + `VoiceService` config instead of raw signals |
| Topology | Build paths from `Device`, `DialPeer`, `Provider`, `VoiceRelationship` |
| UI | Visualize registry contents as deployment graph |

v1 ships the **schema only** — no parser integration or topology building yet.

## Comparison with Canonical Data Model (CDM)

| Aspect | CDM | CVOM |
|--------|-----|------|
| Scope | Investigation lifecycle (Case, Evidence, Hypothesis, Decision) | Voice deployment configuration and state |
| Root aggregate | `Case` | `ObjectRegistry` / `VoiceTopology` |
| Producers | All engines | Parsers primarily |
| Consumers | Runtime, report, learning | Correlation, topology, future UI |
| Vendor neutrality | Metadata extensions | Typed objects with vendor in provenance |

CDM answers *"what happened in this investigation?"*  
CVOM answers *"what does this deployment look like?"*

They complement each other: Evidence links to CVOM objects via `source_evidence_id`.

## Migration plan

1. **v1 (this sprint)** — CVOM schema, registry, tests, docs
2. **v2** — Cisco parsers emit CVOM objects alongside findings
3. **v3** — Correlation rules read CVOM objects
4. **v4** — Topology engine builds `VoiceTopology` from registry
5. **v5** — Microsoft Teams / Ribbon / AudioCodes parsers map to same types

## Package layout

```
core/model/
  voice_graph.py      # VoiceObject, VoiceRelationship
  device.py           # Device
  interface.py        # Interface
  voice_service.py    # VoiceService
  sip_ua.py           # SipUA
  dial_peer.py        # DialPeer
  codec_class.py      # CodecClass
  server_group.py     # ServerGroup
  translation_rule.py # TranslationRule
  translation_profile.py
  provider.py         # Provider
  voice_topology.py   # VoiceTopology container
  object_registry.py  # ObjectRegistry
```

## Tests

`tests/test_voice_object_model.py` covers Device, DialPeer, SipUA, VoiceService, registry lookups, relationships, and immutability.
