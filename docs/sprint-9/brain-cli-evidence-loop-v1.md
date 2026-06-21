# Sprint 9.5 — Brain CLI Evidence Loop v1

## Purpose

VoicePilot Brain orchestrates investigation engines through `RuntimeEngine`, but earlier Brain CLI commands only kept sessions in memory. Each CLI invocation starts a fresh process, so `brain status`, `brain replay`, and related commands could not see sessions created by `brain start` in another terminal.

Sprint 9.5 adds a lightweight local session store and two new commands so Brain can be driven end-to-end across separate CLI processes:

- `voicepilot brain upload SESSION-ID COMMAND FILE`
- `voicepilot brain next SESSION-ID`

Brain remains an orchestrator only. It does not parse CLI output, diagnose faults, or contain vendor-specific logic.

## CLI Workflow

Typical VP-CUBE-0001 flow:

```bash
voicepilot brain start VP-CUBE-0001

voicepilot brain upload BRN-xxxx "show sip-ua status" \
  examples/sample_evidence/parser/show_sip_ua_status_disabled.txt

voicepilot brain next BRN-xxxx

voicepilot brain status BRN-xxxx

voicepilot brain replay BRN-xxxx

voicepilot brain list
```

### Command Summary

| Command | Behavior |
|---------|----------|
| `brain start PLAYBOOK` | Create Brain session + case, persist locally, print first expected evidence |
| `brain upload SESSION COMMAND FILE` | Load session, submit evidence via existing evidence flow, persist |
| `brain next SESSION` | Advance orchestrated pipeline (analyze → hypotheses → correlate → discovery → quality → recommendation when ready) |
| `brain status SESSION` | Load from memory or local store and print current state |
| `brain replay SESSION` | Load from memory or local store and print investigation timeline |
| `brain list` | Merge in-memory and persisted sessions |

### `brain next` quality gate

After investigation quality is evaluated:

- If quality is below the recommendation threshold and the discovery plan recommends another command, Brain returns to `WAITING_FOR_EVIDENCE` and prints the next best command.
- If quality is sufficient, Brain generates a recommendation and may proceed to verification/learning/close when the current architecture supports it safely.

Upload does **not** run analysis automatically. Use `brain next` to advance the pipeline.

## Local Session Storage

Location:

```text
.voicepilot/sessions/
```

Files per session:

| File | Contents |
|------|----------|
| `{session_id}.json` | Brain session metadata (stage, journey, confidence, quality, etc.) |
| `{session_id}.case.pkl` | Pickled `Case` aggregate (dev-only until full JSON round-trip exists) |

Implementation: `core/brain/brain_store.py`

`BrainSessionStore` methods:

- `save(session, case)`
- `load(session_id)`
- `list_sessions()`
- `delete(session_id)`

Properties:

- Directory is created automatically
- Deterministic filenames derived from session ID
- Sensitive metadata keys (`password`, `token`, `secret`, `api_key`, etc.) are stripped before persistence
- Explicitly local/dev-only

## Current Limitations

- Pickle is used for the `Case` aggregate because full JSON deserialization is not yet implemented for the domain model.
- No multi-user concurrency controls; last write wins.
- No encryption at rest.
- No remote or shared persistence; sessions exist only on the local machine.
- Brain does not collect evidence over SSH; files must be uploaded manually.

## Example VP-CUBE-0001 Flow

1. **Start** — Brain creates a case via `RuntimeEngine.start_investigation()`, opens a Brain session in `WAITING_FOR_EVIDENCE`, and suggests the first VP-CUBE evidence command when available.
2. **Upload** — Paste output from `show sip-ua status` (or another command) from a file. Brain records the upload in its journey and persists state.
3. **Next** — Brain runs parser/analysis, hypothesis generation, correlation, discovery planning, and investigation quality evaluation through existing runtime methods.
4. **Status / Replay / List** — Any new CLI process can reload the persisted session and case to show progress or the investigation timeline.

If quality is insufficient after `brain next`, upload the discovery plan’s next recommended command and run `brain next` again.

## Future Upgrade Path

This store is temporary scaffolding. Planned replacements:

- SQLite or PostgreSQL persistence with canonical Case JSON serialization
- REST API session endpoints for web and automation clients
- Web UI workflow on top of shared session storage
- SSH or scheduler-driven evidence collection
- Encrypted, auditable persistence for production deployments

Do not extend the pickle-based store for production use. Treat `.voicepilot/sessions/` as developer convenience only.
