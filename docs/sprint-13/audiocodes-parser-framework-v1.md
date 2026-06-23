# AudioCodes SBC Parser Framework v1

## Purpose

Sprint 13.2 introduces deterministic AudioCodes SBC parsers that convert exported CLI, INI, and XML evidence into AVOM (AudioCodes Voice Object Model) objects.

The framework is read-only: no SSH, no REST API, and no live configuration changes.

## Architecture

```text
Exported AudioCodes Evidence (TXT / INI / XML)
        │
        ▼
AudioCodesSbcParser (detect → parse → validate)
        │
        ▼
ParserResult (structured_data, findings, voice_objects)
        │
        ▼
TopologyBuilder + RelationshipBuilder
        │
        ▼
VoiceTopology (AudioCodes AVOM buckets + relationships)
```

## Package Layout

```text
plugins/audiocodes/parser/sbc/
  _evidence.py          # TXT / INI / XML parsing
  _base.py              # AudioCodesSbcParser base class
  _helpers.py           # Shared metadata helpers
  show_configuration.py
  show_voip_status.py
  show_sip_interface.py
  show_proxy_set.py
  show_ip_group.py
  show_routing_table.py
  show_tls_context.py
  show_certificates.py
  show_media_realm.py
  show_licenses.py
  show_ha_status.py
  show_sip_options.py
```

## Supported Commands

| Command | AVOM Types | Parser ID |
|---------|------------|-----------|
| show configuration | `SBCDevice`, `SRD`, `ManipulationSet`, `MessageManipulation`, `EthernetInterface`, `MediaSecurityProfile` | `audiocodes_show_configuration` |
| show voip status | `SBCDevice` | `audiocodes_show_voip_status` |
| show sip-interface | `SIPInterface` | `audiocodes_show_sip_interface` |
| show proxy-set | `ProxySet`, `ProxyAddress` | `audiocodes_show_proxy_set` |
| show ip-group | `IPGroup`, `IPProfile` | `audiocodes_show_ip_group` |
| show routing-table | `RoutingRule` | `audiocodes_show_routing_table` |
| show tls-context | `TLSContext`, `MediaSecurityProfile` | `audiocodes_show_tls_context` |
| show certificates | `Certificate` | `audiocodes_show_certificates` |
| show media-realm | `MediaRealm` | `audiocodes_show_media_realm` |
| show licenses | `License` | `audiocodes_show_licenses` |
| show ha-status | `HACluster` | `audiocodes_show_ha_status` |
| show sip-options | `SIPMessagePolicy` | `audiocodes_show_sip_options` |

## Evidence Formats

Parsers accept:

- **TXT** — CLI `Key: Value` export output
- **INI** — sectioned configuration export (`[Section]` / `Key=Value`)
- **XML** — structured export with child record elements

Unknown fields are preserved in record metadata.

## AVOM Objects

All 18 AVOM types live in `core/model/audiocodes_objects.py` and are immutable (`frozen=True`):

`SBCDevice`, `SIPInterface`, `MediaRealm`, `ProxySet`, `ProxyAddress`, `IPGroup`, `IPProfile`, `RoutingRule`, `ManipulationSet`, `MessageManipulation`, `TLSContext`, `Certificate`, `SRD`, `EthernetInterface`, `HACluster`, `License`, `SIPMessagePolicy`, `MediaSecurityProfile`

## Registration

```python
from parser.parser_registry import ParserRegistry
from plugins.audiocodes.parser import register_audiocodes_parsers

registry = ParserRegistry()
register_audiocodes_parsers(registry)
```

`build_default_parser_engine()` registers Cisco, Microsoft, and AudioCodes parsers.

## Topology Integration

`TopologyBuilder` partitions AVOM objects into dedicated buckets on `VoiceTopology`.

`RelationshipBuilder` infers:

- IP Group → Proxy Set (`uses`)
- IP Group → Media Realm (`uses`)
- IP Group → IP Profile (`uses`)
- Routing Rule → IP Group (`routes_to`)
- Proxy Set → Proxy Address (`uses`)
- SIP Interface → TLS Context / Media Realm (`uses`)
- TLS Context → Certificate (`uses`)
- Message Manipulation → Manipulation Set (`uses`)

## Sample Evidence

```text
examples/sample_evidence/audiocodes/
```

## Related Tests

- [`../../tests/test_audiocodes_parser_framework.py`](../../tests/test_audiocodes_parser_framework.py) — 52 deterministic tests

## Related Documentation

- [`../../architecture/part-4-platform/13-audiocodes-object-model.md`](../../architecture/part-4-platform/13-audiocodes-object-model.md)
- [`audiocodes-professional-pack-v1.md`](audiocodes-professional-pack-v1.md)
