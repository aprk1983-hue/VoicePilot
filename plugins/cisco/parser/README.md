# Cisco Parser Pack

Cisco IOS / IOS-XE / CUBE CLI parsers for VoicePilot.

## Implemented

| Command | Parser | Status |
|---------|--------|--------|
| `show sip-ua status` | `CiscoShowSipUaStatusParser` | Implemented |

See [docs/parsers/cisco-show-sip-ua-status.md](../../../docs/parsers/cisco-show-sip-ua-status.md).

## Planned Commands

Initial Cisco CUBE / voice troubleshooting targets:

| Command | Parser (planned) |
|---------|------------------|
| `show version` | `ShowVersionParser` |
| `show sip-ua status` | `CiscoShowSipUaStatusParser` | Done |
| `show dial-peer voice summary` | `ShowDialPeerVoiceSummaryParser` |
| `show running-config` | `ShowRunningConfigParser` |
| `debug ccsip messages` | `DebugCcsipMessagesParser` |
| `show call active voice brief` | `ShowCallActiveVoiceBriefParser` |
| `show voice class codec` | `ShowVoiceClassCodecParser` |
| `show license summary` | `ShowLicenseSummaryParser` |
| `show inventory` | `ShowInventoryParser` |
| `show platform` | `ShowPlatformParser` |

## Plugin Boundary

```
plugins/cisco/parser/
  __init__.py              # register parsers with ParserRegistry
  show_sip_ua_status.py    # example future module
  debug_ccsip_messages.py
  ...
```

Cisco parsers:

- Implement `CommandParser` from `parser.interfaces`
- Register via `ParserRegistry.register()` at plugin load time
- Never import or mutate `Case`
- Return `ParserResult` only

## Registration

```python
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers

registry = ParserRegistry()
register_cisco_parsers(registry)
```

## Related

- [Parser framework architecture](../../../docs/parser-framework.md)
- [Cisco plugin README](../README.md)
