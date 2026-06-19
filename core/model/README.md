# Canonical Voice Object Model (CVOM)

CVOM is the vendor-neutral object layer between parsers and VoicePilot engines.

## Purpose

Parsers translate CLI output, configs, and traces into typed, immutable objects — not ad-hoc findings alone. Every enterprise voice platform (Cisco CUBE, Microsoft Teams, Ribbon, AudioCodes, Oracle SBC) maps into the same schema.

## Layout

| Module | Object |
|--------|--------|
| `voice_graph.py` | `VoiceObject` base, `VoiceRelationship` |
| `device.py` | `Device` |
| `interface.py` | `Interface` |
| `voice_service.py` | `VoiceService` |
| `sip_ua.py` | `SipUA` |
| `dial_peer.py` | `DialPeer` |
| `codec_class.py` | `CodecClass` |
| `server_group.py` | `ServerGroup` |
| `translation_rule.py` | `TranslationRule` |
| `translation_profile.py` | `TranslationProfile` |
| `provider.py` | `Provider` |
| `voice_topology.py` | `VoiceTopology` container |
| `object_registry.py` | `ObjectRegistry` lookup |

## Design rules

- Objects are **immutable** after creation (`frozen` dataclasses).
- Parsers **create** objects with provenance (`source_parser`, `source_command`, `source_evidence_id`).
- Correlation, topology, and future UI **read** objects — they do not mutate them.
- No topology building or graph algorithms in this package (v1).

## Usage (future)

```python
from model import DialPeer, ObjectRegistry, SipUA, VoiceService

registry = ObjectRegistry()
sip_ua = SipUA.create(
    vendor="cisco",
    platform="CUBE",
    hostname="cube-edge-01",
    enabled=False,
    source_parser="cisco_show_sip_ua_status",
    source_command="show sip-ua status",
    source_evidence_id="EVD-abc123",
)
registry.register(sip_ua)
```

## Related

- [Canonical Data Model](../../docs/data-model/canonical-data-model.md) — investigation aggregate schema
- [CVOM v1 spec](../../docs/sprint-4/canonical-voice-object-model.md)
