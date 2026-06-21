# 06 — Brain Architecture

> **Status:** Partial — VoicePilot Brain v1 orchestrator implemented under `core/brain/`

## Purpose

Document the relationship between the `brain/` documentation stubs (16 planned engines) and the engines implemented under `core/`. The **VoicePilot Brain** (`core/brain/`) is the orchestration kernel that coordinates runtime engines without implementing troubleshooting logic.

## VoicePilot Brain

The Brain is the operating-system kernel for VoicePilot investigations:

- Creates Brain sessions and cases via `RuntimeEngine`
- Advances deterministic `BrainStage` values
- Delegates all specialist work to existing engines
- Publishes Brain events on the internal `EventBus`
- Records orchestration decisions in the decision log

Implementation: [`../../core/brain/README.md`](../../core/brain/README.md)

## Brain Orchestration

Orchestration flow:

```
Brain Start → WAITING_FOR_EVIDENCE → Parser/Analysis → Hypothesis
  → Correlation → Discovery Planner → Investigation Quality
  → Recommendation → Verification → Learning → COMPLETE
```

The Brain never parses CLI output, diagnoses faults, or generates recommendations.

## Brain Context

`BrainContext` is an immutable read-only snapshot containing references to:

- Case, DiscoveryPlan, InvestigationQualityReport
- HealthReport, KnowledgeReport, Topology
- Decision log, hypotheses, recommendations

The Brain assembles context for status and replay output but does not mutate specialist reports.

## Brain Session

`BrainSession` is an immutable in-memory aggregate:

- Session ID (`BRN-*`), case ID, playbook ID
- Current stage, confidence, quality score
- Journey entries and orchestration decision log IDs

Sessions are stored in `BrainRegistry` and mirrored on `Case.metadata["brain_session"]`.

## Brain State Machine

`BrainStage` enumerates orchestration stages from `INITIALIZING` through `COMPLETE` or `FAILED`. Stage transitions publish `BRAIN_STAGE_CHANGED` events and append journey entries.

## Investigation Replay

Brain replay combines:

1. Brain journey entries (stage transitions)
2. Decision log entries referenced by the session

Formatted by `format_brain_replay()` and exposed via `voicepilot brain replay`.

## Repository Modules Involved

- [`../../core/brain/`](../../core/brain/) — Brain orchestrator (implemented)
- [`../../brain/README.md`](../../brain/README.md) — planned engine documentation stubs
- [`../../core/runtime/runtime_engine.py`](../../core/runtime/runtime_engine.py) — runtime kernel delegated by Brain
- [`../../core/runtime/event_bus.py`](../../core/runtime/event_bus.py) — event bus reused by Brain

## Related Tests

- [`../../tests/test_brain_engine.py`](../../tests/test_brain_engine.py)
- Runtime and engine tests under [`../../tests/`](../../tests/)

## Related Documentation

- [`../../docs/sprint-9/brain-v1.md`](../../docs/sprint-9/brain-v1.md)
- [`../../docs/architecture/voicepilot-brain.md`](../../docs/architecture/voicepilot-brain.md)
- [Part 5 — Brain Engine Roadmap](../part-5-future/05-brain-engine-roadmap.md)

## Cross References

- [Part 2 — Runtime Kernel](03-runtime-kernel.md)
- [Part 3 — Investigation Workflow Engines](../part-3-engines/01-investigation-workflow-engines.md)
- [Part 4 — CLI](../part-4-platform/01-cli.md)
