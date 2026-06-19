# VoicePilot CLI

Terminal interface for VoicePilot investigations.

## v1 Commands

| Command | Purpose |
|---------|---------|
| `voicepilot investigate <playbook_id>` | Run deterministic intake question loop |

## Usage

```bash
pip install -e .
voicepilot investigate VP-CUBE-0001
```

Example session:

```
Investigation started
Case:     CASE-abc123
State:    INTAKE
Playbook: VP-CUBE-0001
[Q-INT-001] Did outbound PSTN calling ever work in this environment?
> yes
[Q-INT-002] When did outbound calling stop working?
> 2026-06-10
...
Intake complete. Next phase: DISCOVERY.
```

## Architecture

The CLI is a thin adapter over `RuntimeEngine` v1:

```
voicepilot investigate
        │
        ▼
run_investigation(playbook_id, input_provider, output_writer)
        │
        ▼
RuntimeEngine.start_investigation() / submit_answer()
        │
        ▼
PluginRegistry → PlaybookCatalog → intake questions
```

- No business logic in the CLI layer
- `run_investigation()` is testable without a real terminal
- Uses Python standard library `argparse` only

## Planned Commands

| Command | Status |
|---------|--------|
| `voicepilot case show` | Future |
| `voicepilot playbook list` | Future |
| `voicepilot plugin list` | Future |

See [CLI v1](../docs/sprint-1/cli-v1.md).
