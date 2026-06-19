# Runtime Engine v1

Sprint 1 deliverable: deterministic intake question execution loop in `RuntimeEngine`.

## Scope

Runtime Engine v1 handles **only** the deterministic intake question flow:

1. Start an investigation from a cataloged playbook ID
2. Present intake questions in playbook order
3. Record answers on the case and timeline
4. Advance to `DISCOVERY` when all `INTAKE`-phase questions are answered

**Not in v1:**

- AI / LLM reasoning
- HTTP API or React UI
- SIP parser or evidence evaluation
- Confidence gates, hypothesis discrimination, or strategy selection
- Discovery-phase execution beyond returning the first discovery question

Those capabilities will layer on top of the same `InvestigationTurn` contract in later sprints.

## API

### `RuntimeEngine.start_investigation(playbook_id: str) -> InvestigationTurn`

1. Loads the playbook from `PlaybookCatalog` (auto-discovers plugins if needed)
2. Creates a new `Case` via `CaseManager`
3. Attaches playbook metadata and parsed intake questions
4. Transitions case state `NEW` → `INTAKE`
5. Returns the first unanswered `INTAKE`-phase question

Raises `PlaybookIdNotFoundError` when the playbook ID is not cataloged.

### `RuntimeEngine.submit_answer(case_id, question_id, answer) -> InvestigationTurn`

1. Stores the answer on the case question and intake metadata (`target_field` from DSL)
2. Appends a `question_answered` timeline event
3. Returns the next question for the current phase
4. When all `INTAKE` questions are answered, transitions to `DISCOVERY` and returns the first `DISCOVERY` question

Raises `CaseNotFoundError` or `QuestionNotFoundError` for invalid IDs.

## Domain Model

`InvestigationTurn` is the runtime contract presented to channels (CLI, API, voice) in future sprints:

| Field | Description |
|-------|-------------|
| `case_id` | Active investigation case |
| `state` | Current `InvestigationState` |
| `prompt` | Question text or phase message |
| `question_id` | Active question ID (may be `None` when waiting) |
| `expected_response_type` | e.g. `text`, `boolean` |
| `available_options` | Multiple-choice options (empty in v1) |
| `required` | Whether the question must be answered |
| `context` | Playbook and question metadata |
| `next_action_type` | e.g. `ask_question`, `await_phase` |

## Flow

```
start_investigation(playbook_id)
        │
        ▼
PlaybookCatalog.get(playbook_id)
        │
        ▼
CaseManager.create_case()  →  INTAKE
        │
        ▼
Return first INTAKE question as InvestigationTurn
        │
        ▼
submit_answer(case_id, question_id, answer)
        │
        ├── more INTAKE questions → next InvestigationTurn
        │
        └── intake complete → DISCOVERY → first DISCOVERY question
```

## Implementation

| Module | Role |
|--------|------|
| `core/runtime/runtime_engine.py` | Public API |
| `core/runtime/intake_flow.py` | Playbook question parsing, answer storage, turn building |
| `core/domain/models.py` | `InvestigationTurn` |

## Tests

`tests/test_runtime_engine.py` covers case creation, first question, answer advancement, intake completion → discovery, and error paths.

```bash
pytest tests/test_runtime_engine.py -v
```

## Next Steps

- Discovery and topology execution loops
- Evidence collection and SIP parser integration
- Reasoning engine and confidence scoring
- `RuntimeEngine` event subscriptions for brain engines
