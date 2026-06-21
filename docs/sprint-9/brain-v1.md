# VoicePilot Brain v1

Epic 3 delivers the VoicePilot Brain — a deterministic orchestration kernel that coordinates existing engines through `RuntimeEngine` without implementing parsing, diagnosis, vendor logic, or recommendation rules.

## Package layout

```
core/brain/
├── brain_models.py       # BrainStage, BrainSession, replay models
├── brain_context.py      # Immutable read-only orchestration context
├── brain_registry.py     # In-memory Brain session registry
├── brain_engine.py       # BrainEngine orchestration
├── brain_report.py       # Status and investigation replay formatters
├── brain_bootstrap.py    # Default engine wiring
└── README.md
```

## Architectural rules

The Brain is an **orchestrator only**. It must never:

- Parse CLI output
- Diagnose faults
- Contain Cisco or Microsoft logic
- Generate recommendations
- Implement troubleshooting rules

Those responsibilities remain with Parser Engine, Analysis Engine, Hypothesis Engine, Correlation Engine, Discovery Planner, Investigation Quality Framework, Recommendation Engine, Verification Engine, and Learning Engine.

## BrainStage

Stages: `INITIALIZING`, `WAITING_FOR_EVIDENCE`, `PARSING`, `ANALYZING`, `CORRELATING`, `DISCOVERY_PLANNING`, `QUALITY_EVALUATION`, `RECOMMENDING`, `VERIFYING`, `LEARNING`, `COMPLETE`, `FAILED`.

## BrainSession

Immutable frozen dataclass tracking:

- `session_id`, `case_id`, `playbook`
- `current_stage`, `started_at`, `last_updated`
- `current_confidence`, `current_quality_score`
- `completed`, `failed`, `decision_log_ids`, `journey`

## BrainContext

Immutable read-only snapshot passed between stages:

- Case, DiscoveryPlan, InvestigationQualityReport
- HealthReport, KnowledgeReport, Topology
- Decision log, hypotheses, recommendations

The Brain never modifies these reports directly.

## Orchestration flow

```
Brain Start → Create Case → WAITING_FOR_EVIDENCE
  → Parser/Analysis (RuntimeEngine.analyze_case)
  → Hypothesis Engine (generate_hypotheses)
  → Correlation Engine (correlate_case)
  → Discovery Planner (plan_discovery)
  → Investigation Quality (evaluate_investigation_quality)
  → Recommendation Engine (generate_recommendation)
  → Verification Engine (submit_verification when RESOLUTION)
  → Learning Engine (close_case_with_learning)
  → COMPLETE
```

## Runtime integration

```python
session = runtime.start_brain_session("VP-CUBE-0001")
result = runtime.advance_brain_session(session.session_id)
context = runtime.brain_engine.build_context(session.session_id)
```

## Event bus

Brain publishes on the existing `EventBus`:

- `BRAIN_SESSION_STARTED`
- `BRAIN_STAGE_CHANGED`
- `BRAIN_WAITING_FOR_EVIDENCE`
- `BRAIN_ANALYSIS_COMPLETED`
- `BRAIN_RECOMMENDATION_READY`
- `BRAIN_COMPLETED`

## CLI

```bash
voicepilot brain start VP-CUBE-0001
voicepilot brain status BRN-abc123
voicepilot brain replay BRN-abc123
voicepilot brain list
```

## Investigation replay

`voicepilot brain replay` generates a chronological timeline combining Brain journey steps and decision log entries where available.

## Limitations

- In-memory sessions only (no database, file persistence, SSH, or REST API)
- No AI or LLM in v1
- Evidence must be uploaded onto the case before `advance_brain_session()` can continue

## Tests

```bash
pytest tests/test_brain_engine.py
pytest
```
