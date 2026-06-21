# VoicePilot Brain

Vendor-neutral orchestration kernel for VoicePilot investigations.

## Purpose

The Brain is the **operating system kernel** for VoicePilot. It orchestrates existing engines through `RuntimeEngine` and never implements parsing, diagnosis, Cisco logic, or recommendation rules.

## Layout

| Module | Responsibility |
|--------|----------------|
| `brain_models.py` | `BrainStage`, `BrainSession`, replay models |
| `brain_context.py` | Immutable read-only orchestration context |
| `brain_registry.py` | In-memory Brain session registry |
| `brain_engine.py` | `BrainEngine` orchestration |
| `brain_report.py` | Status and investigation replay formatters |
| `brain_bootstrap.py` | Default engine wiring |

## Orchestration flow

```
Brain Start → Create Case → WAITING_FOR_EVIDENCE
  → Parser/Analysis (RuntimeEngine.analyze_case)
  → Hypothesis Engine
  → Correlation Engine
  → Discovery Planner
  → Investigation Quality
  → Recommendation Engine
  → Verification Engine
  → Learning Engine
  → COMPLETE
```

## Usage

```python
from brain import BrainEngine, default_brain_engine

brain = default_brain_engine(runtime)
session = brain.start_session("VP-CUBE-0001")
result = brain.advance_session(session.session_id)
context = brain.build_context(session.session_id)
```

## Related

- [Brain v1 spec](../../docs/sprint-9/brain-v1.md)
- [Runtime kernel](../runtime/README.md)
- [Investigation session engine](../investigation/README.md)
