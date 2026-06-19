# Cisco Parser: show run | sec voice service voip

Deterministic parser for Cisco running-config `voice service voip` section output.

## Implementation

| Item | Value |
|------|-------|
| Class | `CiscoShowRunVoiceServiceVoipParser` |
| Location | `plugins/cisco/parser/show_run_voice_service_voip.py` |
| Vendor | `cisco` |
| Command | `show run \| sec voice service voip` |
| Version | `1.0.0` |

## Purpose

Confirms whether SIP-UA / SIP service is disabled in **configuration**, complementing runtime state from `show sip-ua status`.

## Structured Data

| Field | Type | Description |
|-------|------|-------------|
| `voice_service_voip_present` | `bool` | `voice service voip` stanza detected |
| `sip_section_present` | `bool` | `sip` subsection present |
| `sip_ua_disabled_by_config` | `bool \| None` | `no sip` or equivalent disable detected |
| `bind_control_interface` | `str \| None` | `bind control source-interface` value |
| `bind_media_interface` | `str \| None` | `bind media source-interface` value |
| `trusted_ip_list_present` | `bool` | `ip address trusted list` configured |
| `allow_connections_sip_to_sip` | `bool` | `allow-connections sip to sip` present |
| `early_offer_forced` | `bool` | `forced early-offer` detected |
| `options_ping_present` | `bool` | `options-ping` configured |
| `raw_voice_service_lines` | `list[str]` | Parsed config lines (prompt stripped) |

## Findings

| Signal | When emitted |
|--------|----------------|
| `voice_service_voip_present` | Voice service voip config detected |
| `sip_section_present` | SIP subsection present |
| `sip_ua_disabled_by_config` | `no sip` or global disable detected |
| `sip_bind_control_present` | Control bind interface configured |
| `sip_bind_media_present` | Media bind interface configured |
| `trusted_ip_list_present` | Trusted IP list configured |
| `allow_connections_sip_to_sip_present` | SIP-to-SIP connections allowed |
| `early_offer_forced` | Forced early offer configured |
| `options_ping_present` | OPTIONS ping configured |

## Sample Evidence

```
examples/sample_evidence/parser/
├── show_run_voice_service_voip_normal.txt
├── show_run_voice_service_voip_disabled.txt
└── show_run_voice_service_voip_bindings.txt
```

## Analysis Integration

Registered in `register_cisco_parsers()` with parser ID `cisco_show_run_voice_service_voip`.

## Tests

```bash
pytest tests/test_cisco_show_run_voice_service_voip_parser.py -v
```

## Related

- [Cisco show sip-ua status parser](cisco-show-sip-ua-status.md)
- [Parser framework](../parser-framework.md)
