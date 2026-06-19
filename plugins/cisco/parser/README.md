# Cisco Parser Pack

Future home of Cisco IOS / IOS-XE / CUBE CLI parsers for VoicePilot.

## Scope

This directory will contain vendor-specific implementations of the core `CommandParser` interface. **No parsing logic exists yet** — this sprint establishes the plugin boundary only.

## Planned Commands

Initial Cisco CUBE / voice troubleshooting targets:

| Command | Parser (planned) |
|---------|------------------|
| `show version` | `ShowVersionParser` |
| `show sip-ua status` | `ShowSipUaStatusParser` |
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

## Registration (future)

```python
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser.show_sip_ua_status import ShowSipUaStatusParser

def register_cisco_parsers(registry: ParserRegistry) -> None:
    registry.register(ShowSipUaStatusParser())
```

## Related

- [Parser framework architecture](../../../docs/parser-framework.md)
- [Cisco plugin README](../README.md)
