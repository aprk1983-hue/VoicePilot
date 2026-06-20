# Scenario CLI v1

Engineers, sales, and demo users can run VP-CUBE-0001 scenario regression tests directly from the VoicePilot CLI.

## Commands

Run all scenarios for a playbook:

```bash
voicepilot scenarios VP-CUBE-0001
```

Run a single scenario:

```bash
voicepilot scenarios VP-CUBE-0001 --scenario provider_503
```

Write a Markdown report:

```bash
voicepilot scenarios VP-CUBE-0001 --output scenario_results.md
```

## Behavior

- Reuses `core/runtime/scenario_runner.py` shared with `examples/run_vp_cube_0001_scenarios.py`
- Prints a fixed-width summary table:

  `Scenario | Expected Root Cause | Actual Top Hypothesis | Confidence | Pass/Fail`

- Exits with code `0` when all executed scenarios pass
- Exits with code `1` when any scenario fails, the playbook has no scenario pack, or the requested scenario ID is unknown
- With `--scenario`, only the named folder under `examples/sample_evidence/scenarios/vp_cube_0001/` is executed
- With `--output`, writes a Markdown report and prints the saved file path

## Supported playbooks

| Playbook ID | Scenario root |
|-------------|---------------|
| `VP-CUBE-0001` | `examples/sample_evidence/scenarios/vp_cube_0001/` |

## Error handling

- Unknown playbook: `No scenario pack registered for playbook: <id>`
- Unknown scenario: `Scenario '<id>' not found for playbook VP-CUBE-0001. Available: ...`

## Implementation

| Module | Role |
|--------|------|
| `core/runtime/scenario_runner.py` | Shared scenario discovery, execution, and formatting |
| `cli/voicepilot_cli.py` | `scenarios` subcommand and `run_scenario_assessment()` |
| `examples/run_vp_cube_0001_scenarios.py` | Thin wrapper for scripted example execution |

## Tests

```bash
pytest tests/test_cli_scenarios.py
voicepilot scenarios VP-CUBE-0001
voicepilot scenarios VP-CUBE-0001 --scenario provider_503
voicepilot scenarios VP-CUBE-0001 --output scenario_results.md
```
