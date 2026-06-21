# Interactive Investigation Engine v1

Sprint 9.4 adds a deterministic investigation session engine that orchestrates evidence collection using the Discovery Planner and Investigation Quality Framework.

## Package layout

```
core/investigation/
├── session_models.py          # InvestigationSession, journey entries, enums
├── session_registry.py        # In-memory session registry
├── session_state_machine.py   # Session status/action validation
├── session_engine.py          # InvestigationSessionEngine
├── session_report.py          # Journey Markdown formatters
├── session_bootstrap.py       # Default engine wiring
└── README.md
```

## Models

### InvestigationSession

Immutable session aggregate:

- `session_id`, `case_id`, `playbook_id`
- `status` — `ACTIVE`, `AWAITING_INPUT`, `COMPLETED`, `FAILED`
- `current_action` — orchestration step (intake, discovery, evidence, analysis, quality, etc.)
- `case_state` — mirrors `Case.status`
- `journey` — chronological `SessionJourneyEntry` records
- pending question/evidence fields for interactive prompts

### SessionJourneyEntry

Records each orchestration step with sequence, timestamp, action, case state, and summary.

## Session engine flow

```
start_session(playbook_id)
  → intake questions
  → discovery planning (plan_discovery)
  → required evidence collection
  → analysis → hypothesis → correlation
  → quality evaluation (evaluate_investigation_quality)
  → optional discovery-guided evidence when quality < threshold
  → recommendation → verification → closure
```

The engine stores journey metadata on `Case.metadata["investigation_session"]` for incident reports.

## Runtime integration

```python
session = runtime.start_investigation_session("VP-CUBE-0001")
result = runtime.continue_investigation_session(session.session_id, input_provider=input_fn)
status = runtime.format_investigation_session_status(session.session_id)
```

## CLI commands

Start a full interactive investigation (prints session ID):

```bash
voicepilot investigate VP-CUBE-0001
```

Show session status:

```bash
voicepilot status SES-abc123
```

Continue from the next input boundary:

```bash
voicepilot continue SES-abc123
```

## Incident report section

Closed-case reports include:

```markdown
## Investigation Journey
```

When a session exists, the report lists the session ID and chronological journey steps.

## Limitations

- Sessions and cases remain in-memory only within a single process
- `status` and `continue` require the same runtime process that created the session (or an injected engine in tests)
- No AI, FastAPI, or file/database persistence in v1

## Tests

```bash
pytest tests/test_investigation_session_engine.py
pytest
```
