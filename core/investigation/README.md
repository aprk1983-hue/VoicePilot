# Investigation Session Engine

Deterministic, interactive orchestration of VoicePilot investigations using the Discovery Planner and Investigation Quality Framework.

## Purpose

Break monolithic CLI flows into resumable investigation sessions with explicit journey tracking — no AI, no persistence in v1.

## Layout

| Module | Responsibility |
|--------|----------------|
| `session_models.py` | `InvestigationSession`, `SessionJourneyEntry`, status/action enums |
| `session_registry.py` | In-memory session registry |
| `session_state_machine.py` | Session status and action validation |
| `session_engine.py` | `InvestigationSessionEngine` orchestration |
| `session_report.py` | Journey Markdown formatters |
| `session_bootstrap.py` | Default engine wiring |

## Usage

```python
from investigation import InvestigationSessionEngine

engine = InvestigationSessionEngine(runtime)
session = engine.start_session("VP-CUBE-0001")
result = engine.continue_session(session.session_id, input_provider=input_fn)
print(engine.format_session_status(session.session_id))
```

## Orchestration flow

1. Intake questions
2. Discovery planning (`plan_discovery`)
3. Required evidence collection
4. Analysis → hypothesis → correlation
5. Investigation quality evaluation (`evaluate_investigation_quality`)
6. Optional discovery-guided evidence when quality is below threshold
7. Recommendation → verification → closure

## Related

- [Interactive investigation engine v1 spec](../../docs/sprint-9/interactive-investigation-engine-v1.md)
- [Discovery planner](../discovery/README.md)
- [Investigation quality](../investigation_quality/README.md)
