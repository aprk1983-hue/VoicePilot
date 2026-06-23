# 13 — AudioCodes SBC Object Model

> **Status:** Implemented

## Purpose

Document the AudioCodes Voice Object Model (AVOM) and deterministic parser framework that converts exported SBC evidence into immutable canonical objects for topology and investigation workflows.

This sprint delivers read-only parsing only. No SSH, REST API, or configuration changes are included.

## Repository Modules Involved

- AVOM types: [`../../core/model/audiocodes_objects.py`](../../core/model/audiocodes_objects.py)
- Object type constants: [`../../core/model/voice_graph.py`](../../core/model/voice_graph.py)
- Parsers: [`../../plugins/audiocodes/parser/sbc/`](../../plugins/audiocodes/parser/sbc/)
- Topology: [`../../core/topology/topology_builder.py`](../../core/topology/topology_builder.py)
- Relationships: [`../../core/topology/relationship_builder.py`](../../core/topology/relationship_builder.py)
- Bootstrap: [`../../core/runtime/parser_bootstrap.py`](../../core/runtime/parser_bootstrap.py)

## Pipeline

```text
Exported Evidence (TXT / INI / XML) → AudioCodes Parsers → AVOM Objects → VoiceTopology → Future Investigation Engine
```

## AVOM Inventory

| Class | `object_type` |
|-------|---------------|
| `SBCDevice` | `audiocodes_sbc_device` |
| `SIPInterface` | `audiocodes_sip_interface` |
| `MediaRealm` | `audiocodes_media_realm` |
| `ProxySet` | `audiocodes_proxy_set` |
| `ProxyAddress` | `audiocodes_proxy_address` |
| `IPGroup` | `audiocodes_ip_group` |
| `IPProfile` | `audiocodes_ip_profile` |
| `RoutingRule` | `audiocodes_routing_rule` |
| `ManipulationSet` | `audiocodes_manipulation_set` |
| `MessageManipulation` | `audiocodes_message_manipulation` |
| `TLSContext` | `audiocodes_tls_context` |
| `Certificate` | `audiocodes_certificate` |
| `SRD` | `audiocodes_srd` |
| `EthernetInterface` | `audiocodes_ethernet_interface` |
| `HACluster` | `audiocodes_ha_cluster` |
| `License` | `audiocodes_license` |
| `SIPMessagePolicy` | `audiocodes_sip_message_policy` |
| `MediaSecurityProfile` | `audiocodes_media_security_profile` |

## Parser Commands

12 deterministic parsers registered under vendor `audiocodes`:

`show configuration`, `show voip status`, `show sip-interface`, `show proxy-set`, `show ip-group`, `show routing-table`, `show tls-context`, `show certificates`, `show media-realm`, `show licenses`, `show ha-status`, `show sip-options`

## Related Tests

- [`../../tests/test_audiocodes_parser_framework.py`](../../tests/test_audiocodes_parser_framework.py)

## Related Documentation

- [`../../docs/sprint-13/audiocodes-parser-framework-v1.md`](../../docs/sprint-13/audiocodes-parser-framework-v1.md)
- [12 — AudioCodes SBC Knowledge Library](12-audiocodes-knowledge-library.md)

## Cross References

- [04 — Knowledge Packs](04-knowledge-packs.md)
- [09 — Microsoft Teams Parser Pipeline](09-microsoft-teams-parser-pipeline.md)
