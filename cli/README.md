# VoicePilot CLI

Command-line interface for VoicePilot (future).

## Planned Commands

| Command | Purpose |
|---------|---------|
| `voicepilot case open` | Open a new investigation case |
| `voicepilot case show` | Display case state and next action |
| `voicepilot playbook list` | List playbooks from installed plugins |
| `voicepilot plugin list` | List installed plugins and capabilities |
| `voicepilot investigate` | Run investigation loop against a case |

## Status

**Not implemented.** This directory reserves the CLI package layout for a future sprint.

CLI will consume:

- `core/` — runtime kernel
- `sdk/` — plugin discovery
- `plugins/` — official and installed plugins

## Design Notes

- CLI is a thin adapter over application use cases
- No business logic in CLI layer
- Engineer remains in control of destructive actions
