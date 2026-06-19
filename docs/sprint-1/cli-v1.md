# CLI v1

Sprint 1 deliverable: terminal intake investigation via `voicepilot investigate`.

## Scope

CLI v1 starts an investigation from a cataloged playbook ID and runs the deterministic intake question loop implemented by [Runtime Engine v1](runtime-engine-v1.md).

**In v1:**

- Discover plugins from `plugins/`
- Load playbooks via `PlaybookCatalog`
- Start investigation with `RuntimeEngine.start_investigation()`
- Present intake questions and accept answers
- Stop when case state reaches `DISCOVERY`

**Not in v1:**

- AI / reasoning
- HTTP API or React UI
- SIP parser or evidence collection
- Discovery-phase question loop (only completion message)

## Command

```bash
voicepilot investigate VP-CUBE-0001
```

### Behavior

1. `PluginRegistry.discover()` loads manifests under `plugins/`
2. `PlaybookCatalog.load_all()` indexes playbooks by ID
3. `RuntimeEngine.start_investigation(playbook_id)` creates a case and returns the first intake question
4. CLI prints case metadata and the question
5. User answers at the `>` prompt
6. `RuntimeEngine.submit_answer()` records the answer and returns the next question
7. When intake is complete, state transitions to `DISCOVERY` and CLI prints:

   ```
   Intake complete. Next phase: DISCOVERY.
   ```

Unknown playbook IDs print an error and exit with code `1`.

## Testable API

`cli/voicepilot_cli.py` exposes `run_investigation()` for tests and automation:

```python
from cli.voicepilot_cli import run_investigation

output: list[str] = []
answers = iter(["yes", "2026-06-10", "no", "all", "yes"])

code = run_investigation(
    "VP-CUBE-0001",
    input_provider=lambda: next(answers),
    output_writer=output.append,
)
```

| Parameter | Role |
|-----------|------|
| `playbook_id` | Cataloged playbook ID |
| `input_provider` | Callable returning the next answer string |
| `output_writer` | Callable receiving each output line |
| `plugins_root` | Optional plugins directory override |
| `engine` | Optional pre-built `RuntimeEngine` for tests |

Returns exit code `0` on success, `1` when the playbook is not found.

## Entry Point

`pyproject.toml`:

```toml
[project.scripts]
voicepilot = "cli.voicepilot_cli:main"
```

## Tests

`tests/test_cli.py` covers investigation start, first question output, fake input progression, discovery transition, and unknown playbook errors.

```bash
pytest tests/test_cli.py -v
```

## Next Steps

- `voicepilot playbook list` and `voicepilot plugin list`
- Discovery and topology execution loops in CLI
- Case resume and `voicepilot case show`
