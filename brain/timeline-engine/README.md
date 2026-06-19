# Timeline Engine

## Purpose

The Timeline Engine builds and maintains the authoritative chronological record of every investigation. Voice operations incidents unfold over time: symptoms appear, changes occur, evidence is collected, hypotheses shift, decisions are made, fixes are applied, and verification completes. The Timeline Engine captures this sequence as structured events, not as a chat transcript.

A senior TAC engineer reconstructs incident timelines before writing an RCA. This engine does that continuously and automatically from engine events.

## Responsibilities

- Record timestamped investigation events in chronological order.
- Track lifecycle milestones: case opened, symptoms reported, topology identified, evidence collected, hypothesis changes, decisions made, root cause confirmed, fix applied, verification completed, case closed.
- Ingest events from all Brain engines with consistent event schema.
- Correlate events with Case State snapshots at key moments.
- Detect timeline gaps and anomalies (e.g., evidence collected before topology defined).
- Support relative ordering when absolute timestamps are unavailable or disputed.
- Provide timeline views for Report Engine and engineer review.
- Align investigation events with external change windows and symptom onset.
- Preserve immutable event history; corrections create amendment events, not deletions.
- Enable post-incident review boards to replay investigation progression.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case Lifecycle Events | Investigation Engine, State Machine | State transitions, case open/close |
| Symptom & Intake Events | Question Engine, Investigation Engine | Symptom reported, intake completed |
| Topology Events | Topology Engine | Topology identified, updated, validated |
| Evidence Events | Evidence Engine | Artifact collected, parsed, superseded |
| Hypothesis Events | Reasoning Engine | Created, ranked, eliminated, confirmed |
| Decision Events | Decision Engine | All recorded technical decisions |
| Strategy Events | Investigation Planner | Strategy selected, switched |
| Confidence Events | Confidence Engine | Score changes, gate pass/fail |
| Resolution Events | Investigation Engine | Root cause confirmed, fix applied |
| Verification Events | Investigation Engine, Playbook Engine | Test steps completed |
| Engineer Actions | Investigation Engine | Manual annotations, deferrals, overrides |
| External Correlation | Integration (future) | Change management tickets, monitoring alerts |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Investigation Timeline | Case State, Report Engine | Ordered event sequence |
| Milestone Summary | Report Engine, Executive Summary | Key timestamps and durations |
| Event Feed | Engineer Interface | Real-time investigation progression |
| Gap Analysis | Investigation Planner | Unexplained timeline gaps |
| Duration Metrics | Learning Engine | Time-to-intake, time-to-root-cause, time-to-close |
| Correlation View | Reasoning Engine | Change events vs. symptom onset |
| Audit Export | Compliance | Immutable chronological record |

## Internal State

- **Event Registry** — append-only ordered event log per `case_id`.
- **Milestone Tracker** — first occurrence timestamp for each milestone type.
- **Event Schema Registry** — valid event types, required fields, source engines.
- **Ordering Resolver** — handles clock skew and partial ordering conflicts.
- **Snapshot Index** — pointers to Case State snapshots at major milestones.
- **Gap Detector** — rules for expected event sequences and missing milestones.
- **Duration Calculator** — cached phase durations updated on each event.

### Event Record Structure

```yaml
event_id:
case_id:
sequence:
timestamp:
event_type:
source_engine:
summary:
details:              # type-specific payload
related_entities:     # evidence_id, hypothesis_id, decision_id, etc.
case_state_snapshot_ref:  # optional, for major milestones
engineer_visible: true
```

### Standard Milestone Event Types

| Event Type | Typical Source |
|------------|----------------|
| `case_opened` | Investigation Engine |
| `symptom_reported` | Investigation Engine |
| `intake_completed` | Question Engine |
| `topology_identified` | Topology Engine |
| `topology_updated` | Topology Engine |
| `evidence_collected` | Evidence Engine |
| `evidence_parsed` | Evidence Engine |
| `hypothesis_created` | Reasoning Engine |
| `hypothesis_eliminated` | Reasoning Engine |
| `hypothesis_confirmed` | Reasoning Engine |
| `decision_recorded` | Decision Engine |
| `strategy_selected` | Investigation Planner |
| `strategy_switched` | Investigation Planner |
| `confidence_updated` | Confidence Engine |
| `confidence_gate_passed` | Confidence Engine |
| `confidence_gate_failed` | Confidence Engine |
| `state_transition` | State Machine |
| `root_cause_confirmed` | Investigation Engine |
| `fix_applied` | Investigation Engine |
| `verification_completed` | Investigation Engine |
| `case_closed` | Investigation Engine |

## Interactions With Other Engines

- **Investigation Engine** — primary event source for case lifecycle and engineer actions.
- **State Machine** — state transition events with from/to states and gate context.
- **Decision Engine** — every decision creates a timeline event.
- **Evidence Engine** — collection and parsing events with artifact references.
- **Reasoning Engine** — hypothesis lifecycle events.
- **Investigation Planner** — strategy events.
- **Confidence Engine** — score and gate events.
- **Topology Engine** — topology identification and validation events.
- **Question Engine** — intake milestone and significant Q&A events.
- **Report Engine** — primary consumer of timeline for incident documentation.
- **Learning Engine** — duration metrics and event patterns from closed cases.
- **Investigation Graph** — timeline events may reference graph node creation.

## MVP Workflow for VP-CUBE-0001: Outbound Calls Fail

| Time | Event | Source |
|------|-------|--------|
| 09:00 | `case_opened` — VP-CUBE-0001 outbound PSTN failure | Investigation Engine |
| 09:02 | `symptom_reported` — all outbound failing, fast busy | Investigation Engine |
| 09:05 | `strategy_selected` — Routing-first | Investigation Planner |
| 09:20 | `intake_completed` — worked until yesterday; dial-peer edit afternoon prior | Question Engine |
| 09:25 | `topology_identified` — CUCM → CUBE → ITSP | Topology Engine |
| 09:30 | `state_transition` — NEW → INTAKE → TOPOLOGY → COLLECTION | State Machine |
| 09:45 | `evidence_collected` — E-001 show sip-ua status | Evidence Engine |
| 10:00 | `evidence_collected` — E-002 debug ccsip messages | Evidence Engine |
| 10:05 | `evidence_parsed` — local 404 detected | Evidence Engine |
| 10:10 | `hypothesis_created` — dial-peer mismatch, provider rejection, trunk down | Reasoning Engine |
| 10:15 | `decision_recorded` — DEC-002 eliminate trunk down | Decision Engine |
| 10:18 | `decision_recorded` — DEC-003 eliminate provider rejection | Decision Engine |
| 10:22 | `hypothesis_eliminated` — trunk down, provider rejection | Reasoning Engine |
| 10:30 | `state_transition` — COLLECTION → ANALYSIS → HYPOTHESIS → INVESTIGATION | State Machine |
| 11:00 | `evidence_collected` — E-005 dial-peer config | Evidence Engine |
| 11:30 | `confidence_updated` — 72 → 92 | Confidence Engine |
| 11:45 | `root_cause_confirmed` — mobile dial-peer gap | Investigation Engine |
| 11:45 | `decision_recorded` — DEC-006 confirm root cause | Decision Engine |
| 11:45 | `confidence_gate_passed` — threshold 85 | Confidence Engine |
| 12:00 | `fix_applied` — dial-peer added for mobile prefix | Investigation Engine |
| 12:30 | `verification_completed` — local, mobile pass | Investigation Engine |
| 12:45 | `case_closed` | Investigation Engine |

Report Engine consumes this timeline for the Investigation Timeline section. Learning Engine extracts: time-to-root-cause 2h 45m.

## Future Extensions

- External event ingestion: monitoring alerts, syslog timestamps, change management tickets.
- Multi-timezone normalization for global operations teams.
- Timeline replay mode for training and post-incident review.
- Visual timeline export for executive briefing.
- Automated correlation: "symptom onset preceded nearest change by 4 hours."
- SLA breach markers on timeline based on severity policy.
- Branch timelines for multi-engineer parallel investigation merged at sync points.
- Diff view: expected playbook timeline vs. actual investigation timeline.

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Missing events | Incomplete timeline, audit gaps | All engines required to emit events; gap detector alerts Investigation Engine |
| Clock skew | Incorrect event ordering | Ordering resolver uses sequence numbers as primary order; timestamp as secondary |
| Event deletion attempt | Audit integrity violation | Append-only registry; amendments only via new events |
| Duplicate events | Timeline noise | Idempotency keys on event submission from source engines |
| Orphan events | Events without case context | Validation rejects events without valid `case_id` |
| Overwhelming granularity | Engineer cannot find milestones | Milestone summary layer filters detail events for summary views |

## Design Principles

1. **Events, not chat** — Timeline records structured investigation events, not conversation turns.
2. **Chronological truth** — The timeline reflects what happened when, auditable by third parties.
3. **All engines contribute** — Every Brain engine is an event producer with schema compliance.
4. **Immutable history** — Corrections are amendment events; original events preserved.
5. **Milestone clarity** — Standard milestone types enable cross-case duration analytics.
6. **Never guess timestamps** — If time is unknown, mark `timestamp_confidence: estimated` explicitly.
7. **State maintained** — Timeline is part of Case State, persisted across sessions.
8. **Engineer in control** — Engineer may add manual timeline annotations with attribution.
