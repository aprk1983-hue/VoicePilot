# Parser to CVOM: Cisco SIP-UA Status

First parser integration with the Canonical Voice Object Model (CVOM).

## Flow

```
show sip-ua status (CLI output)
        ↓
CiscoShowSipUaStatusParser.parse()
        ↓
ParserResult
  ├── findings[]          (existing signals)
  └── voice_objects[]     (SipUA)
        ↓
AnalysisEngine.analyze()
        ↓
AnalysisFinding.metadata.related_voice_object_ids
```

## SipUA mapping

| CVOM field | Parser source |
|------------|---------------|
| `enabled` | `structured_data.sip_ua_enabled` |
| `registered` | `registration_state == "registered"` |
| `registrar` | `structured_data.registrar_host` |
| `transport` | `structured_data.transport` (null when unknown) |
| `tls` | `transport == "tls"` |
| `source_parser` | `cisco_show_sip_ua_status` |
| `source_command` | `show sip-ua status` |
| `source_evidence_id` | `ParserContext.evidence_id` |
| `confidence` | parser result confidence score |

## ParserResult extension

`ParserResult.voice_objects` holds immutable `VoiceObject` instances. Parsers still return only `ParserResult` — no direct `Case` mutation.

## AnalysisEngine linkage

When `ParserResult.voice_objects` is non-empty, each `AnalysisFinding` from that parse includes:

```json
"related_voice_object_ids": ["VOBJ-abc123..."]
```

Topology building and `ObjectRegistry` registration are deferred to a later sprint.

## Samples

| Sample file | SipUA highlights |
|-------------|------------------|
| `show_sip_ua_status_disabled.txt` | `enabled=false`, `registered=false` |
| `show_sip_ua_status_registered_tls.txt` | `enabled=true`, `registered=true`, `transport=tls`, `tls=true` |

## Next steps

- Register voice objects on `Case` or `ObjectRegistry` during analysis
- Correlation rules read `SipUA.enabled` instead of signal-only matching
- Dial-peer and voice-service parsers emit `DialPeer` and `VoiceService` objects
