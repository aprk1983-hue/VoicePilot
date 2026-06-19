# Cisco Voice Plugin

Official VoicePilot plugin for Cisco voice platform investigations.

## Manifest

See [`manifest.yaml`](manifest.yaml):

| Field | Value |
|-------|-------|
| name | `cisco` |
| display_name | Cisco Voice Plugin |
| version | `0.1.0` |
| plugin_type | `vendor` |
| capabilities | `cube_playbooks`, `cucm_playbooks_future`, `sip_troubleshooting` |
| supported_platforms | Cisco CUBE, Cisco CUCM |

## Playbooks

| Playbook | Path | Scenario |
|----------|------|----------|
| VP-CUBE-0001 | `playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml` | Outbound PSTN calls fail (CUCM → CUBE → ITSP) |

## How It Works

1. **Manifest** declares playbook entry points relative to this directory.
2. **Core `PlaybookLoader`** loads `.vpb.yaml` files by absolute path (today) or via future `PlaybookProvider` (tomorrow).
3. **Runtime** binds playbook to `Case` at intake; engines evaluate DSL rules.
4. **No Cisco logic in core** — all Cisco-specific content lives in this plugin tree.

## Investigation Topology

```
Cisco CUCM → Cisco CUBE → ITSP/PSTN
```

## Future

- CUCM playbooks (`cucm_playbooks_future` capability)
- Cisco parser pack for `debug ccsip messages`
- Knowledge items linked to Cisco bug scrub / field notices
- Expressway and Webex Calling plugin splits if needed

## Related

- [Human-readable playbook doc](../../docs/playbooks/cube/vp-cube-0001-outbound-calls-fail.md)
- [DSL specification](../../docs/dsl/voicepilot-dsl.md)
