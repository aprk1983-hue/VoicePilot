# Parser to CVOM: Cisco Voice Service Voip

CVOM integration for `show run | sec voice service voip` running configuration.

## Flow

```
show run | sec voice service voip
        ↓
CiscoShowRunVoiceServiceVoipParser.parse()
        ↓
ParserResult
  ├── findings[]          (config signals)
  └── voice_objects[]     (VoiceService)
        ↓
AnalysisEngine.analyze()
        ↓
AnalysisFinding.metadata.related_voice_object_ids
```

## VoiceService mapping

| CVOM field | Parser source |
|------------|---------------|
| `allow_connections` | `allow_connections_sip_to_sip` |
| `bind_control` | `bind_control_interface` |
| `bind_media` | `bind_media_interface` |
| `trusted_ips` | `trusted_ips` list (ipv4 network + mask) |
| `early_offer` | `early_offer_forced` |
| `options_ping` | `options_ping_present` |
| `supplementary_services` | detected `no supplementary-service` lines |
| `source_parser` | `cisco_show_run_voice_service_voip` |
| `source_command` | `show run | sec voice service voip` |
| `source_evidence_id` | `ParserContext.evidence_id` |
| `confidence` | parser result confidence |

`metadata` on the VoiceService object also carries `sip_ua_disabled_by_config` and `sip_section_present` for correlation without mutating the Case.

## Structured data improvements

- `trusted_ips`: `list[str]` of `"{network} {mask}"` entries parsed from `ipv4` lines
- `trusted_ip_list_present`: derived boolean for backward-compatible findings
- `supplementary_services`: list of full config lines when `no supplementary-service sip moved-temporarily` or `refer` appear

## Samples

| Sample | VoiceService highlights |
|--------|-------------------------|
| `show_run_voice_service_voip_disabled.txt` | `sip_ua_disabled_by_config` in metadata; finding still emitted |
| `show_run_voice_service_voip_bindings.txt` | bind control/media, options-ping, early-offer, trusted IPs |
| `show_run_voice_service_voip_normal.txt` | allow-connections, supplementary-service disables |

## Next steps

- Register VoiceService objects on `ObjectRegistry` during analysis
- Correlate `SipUA.enabled` with `VoiceService.metadata.sip_ua_disabled_by_config`
- Extend dial-peer parser to emit `DialPeer` CVOM objects
