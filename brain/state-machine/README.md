# State Machine

## Purpose

The State Machine governs the investigation lifecycle for VoicePilot. It defines valid states, entry and exit conditions, allowed transitions, and failure conditions for every case. No engine may advance an investigation phase without State Machine authorization. This enforces TAC discipline: intake before collection, evidence before conclusion, verification before closure.

The State Machine is the constitutional layer of the VoicePilot Brain.

## Responsibilities

- Define the canonical investigation lifecycle state model.
- Validate transition requests against entry conditions, exit conditions, and allowed paths.
- Reject invalid transitions with explicit failure reasons for Investigation Engine action.
- Enforce gate dependencies: confidence thresholds, evidence completeness, playbook completion.
- Record immutable transition history with timestamps, triggering engine, and rationale.
- Support controlled rollback to prior states when investigation scope materially changes.
- Emit lifecycle events to Report Engine, Learning Engine, and audit systems.
- Prevent case closure from any state except through `VERIFICATION` → `LEARNING` → `CLOSED`.
- Coordinate parallel sub-states where needed (e.g., topology refinement during `COLLECTION`).

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Transition Request | Investigation Engine | Target state with triggering action and context |
| Gate Results | Confidence Engine | Pass/fail for confidence-dependent transitions |
| Evidence Coverage | Evidence Engine | Mandatory evidence satisfaction status |
| Playbook Completion | Playbook Engine | Verification and learning criteria status |
| Topology Validation | Topology Engine | Minimum topology completeness for phase |
| Rollback Request | Investigation Engine | Scope change with documented rationale |
| Failure Signal | Any Engine | Condition that forces transition to failure handling |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Transition Approval | Investigation Engine | Authorized state change with new `status` |
| Transition Rejection | Investigation Engine | Failure reason and remediation requirements |
| Lifecycle Events | Audit, Report Engine | State change records |
| Current State | Case State | Authoritative `status` field |
| Allowed Transitions | Investigation Engine | Valid next states from current position |
| Failure Conditions | Investigation Engine | Active blockers preventing advancement |

## Internal State

- **State Definition Registry** — all states with entry, exit, and timeout policies.
- **Transition Matrix** — allowed edges with guard conditions.
- **Per-Case State History** — append-only transition log per `case_id`.
- **Active Guard Status** — cached evaluation of gate conditions per case.
- **Rollback Policy** — which states permit rollback and maximum rollback depth.
- **Sub-State Registry** — optional nested states for complex phases.

## Investigation Lifecycle States

| State | Purpose |
|-------|---------|
| `NEW` | Case created; minimal metadata captured |
| `INTAKE` | Symptom clarification, impact assessment, initial facts |
| `DISCOVERY` | Scope expansion, affected systems, change correlation |
| `TOPOLOGY` | Voice path modeling and validation |
| `COLLECTION` | Evidence gathering per playbook requirements |
| `ANALYSIS` | Evidence parsing, signal extraction, initial pattern matching |
| `HYPOTHESIS` | Active hypothesis management and discrimination |
| `INVESTIGATION` | Targeted diagnostic actions, iterative evidence loop |
| `RESOLUTION` | Root cause recorded, fix documented |
| `VERIFICATION` | Post-resolution testing and regression checks |
| `LEARNING` | Structured knowledge capture before closure |
| `CLOSED` | Terminal state; case immutable except audit annotations |

## State Definitions

### NEW

**Entry Conditions:** Case creation request accepted by Investigation Engine.

**Exit Conditions:** `case_id` assigned, symptom recorded, severity assigned.

**Allowed Transitions:** → `INTAKE`

**Failure Conditions:** Missing mandatory creation fields.

---

### INTAKE

**Entry Conditions:** Transition from `NEW`; playbook selection initiated.

**Exit Conditions:** Intake questions answered or explicitly deferred with waiver; business impact documented; initial timeline captured.

**Allowed Transitions:** → `DISCOVERY`, → `TOPOLOGY` (if scope already known)

**Failure Conditions:** Symptom undefined; no engineer assigned.

---

### DISCOVERY

**Entry Conditions:** Intake minimum satisfied.

**Exit Conditions:** Affected scope identified; recent changes documented or ruled out; platform confirmed.

**Allowed Transitions:** → `TOPOLOGY`, → `COLLECTION` (if topology pre-validated)

**Failure Conditions:** Contradictory scope statements unresolved.

---

### TOPOLOGY

**Entry Conditions:** Platform and affected scope known.

**Exit Conditions:** Topology Engine reports minimum completeness; voice path from origin to PSTN/provider modeled.

**Allowed Transitions:** → `COLLECTION`, → `DISCOVERY` (rollback on scope change)

**Failure Conditions:** Critical path components unidentified after maximum discovery effort.

---

### COLLECTION

**Entry Conditions:** Topology minimum complete; playbook bound.

**Exit Conditions:** Mandatory evidence collected or waived with documented rationale and investigation lead approval.

**Allowed Transitions:** → `ANALYSIS`, → `TOPOLOGY` (rollback)

**Failure Conditions:** Zero evidence collected with no waiver; collection timeout with no progress.

---

### ANALYSIS

**Entry Conditions:** Minimum evidence available for parsing.

**Exit Conditions:** Evidence Engine parsing complete; initial signals extracted.

**Allowed Transitions:** → `HYPOTHESIS`, → `COLLECTION` (additional evidence required)

**Failure Conditions:** Evidence unparsable with no alternative collection path.

---

### HYPOTHESIS

**Entry Conditions:** Parsed signals available.

**Exit Conditions:** At least one active hypothesis generated; elimination cycle initiated.

**Allowed Transitions:** → `INVESTIGATION`, → `COLLECTION`

**Failure Conditions:** No viable hypotheses and no collection plan to generate discrimination.

---

### INVESTIGATION

**Entry Conditions:** Active hypotheses under evaluation.

**Exit Conditions:** Leading hypothesis confirmed with confidence gate pass OR investigation escalated with documented stall.

**Allowed Transitions:** → `HYPOTHESIS`, → `COLLECTION`, → `RESOLUTION` (confidence gate pass)

**Failure Conditions:** Investigation stall: no progress across N cycles with no new evidence or questions.

---

### RESOLUTION

**Entry Conditions:** Confidence gate PASS for root cause declaration; leading hypothesis status `confirmed`.

**Exit Conditions:** `root_cause` and `resolution` recorded with evidence references.

**Allowed Transitions:** → `VERIFICATION`, → `INVESTIGATION` (rollback on confidence regression)

**Failure Conditions:** Root cause recorded without evidence links; confidence gate FAIL.

---

### VERIFICATION

**Entry Conditions:** Resolution documented.

**Exit Conditions:** Playbook verification checklist complete; all tests passed or failures documented with remediation.

**Allowed Transitions:** → `LEARNING`, → `RESOLUTION` (fix incomplete)

**Failure Conditions:** Critical verification step failed without remediation plan.

---

### LEARNING

**Entry Conditions:** Verification passed.

**Exit Conditions:** Learning Engine acknowledges structured capture; lessons learned recorded.

**Allowed Transitions:** → `CLOSED`

**Failure Conditions:** Learning capture rejected due to missing mandatory fields.

---

### CLOSED

**Entry Conditions:** Learning phase complete; Report Engine final report generated.

**Exit Conditions:** Terminal. No outbound transitions.

**Allowed Transitions:** None

**Failure Conditions:** N/A

## Lifecycle Diagram

```
NEW → INTAKE → DISCOVERY → TOPOLOGY → COLLECTION → ANALYSIS
                                                      ↓
CLOSED ← LEARNING ← VERIFICATION ← RESOLUTION ← INVESTIGATION
                                                      ↑
                                                 HYPOTHESIS
```

Rollback edges (dotted conceptually): any state from `TOPOLOGY` through `RESOLUTION` may rollback to `COLLECTION`, `TOPOLOGY`, or `DISCOVERY` on documented scope change.

## Interactions

- **Investigation Engine** — sole requestor of transitions; executes approved state changes in Case State.
- **Confidence Engine** — guards `INVESTIGATION` → `RESOLUTION` and `RESOLUTION` → `VERIFICATION`.
- **Evidence Engine** — guards `COLLECTION` → `ANALYSIS` and blocks `RESOLUTION` if mandatory gaps remain.
- **Playbook Engine** — guards `VERIFICATION` → `LEARNING` and `LEARNING` → `CLOSED`.
- **Topology Engine** — guards `TOPOLOGY` → `COLLECTION`.
- **Report Engine** — triggered on `RESOLUTION`, `VERIFICATION`, and `CLOSED` entry.
- **Learning Engine** — triggered on `LEARNING` entry; must acknowledge before `CLOSED`.

## Future Extensions

- Parallel branch states for multi-site investigations with synchronized merge gates.
- SLA timers per state with automatic escalation events.
- State machine versioning for backward compatibility with historical cases.
- External workflow integration (ServiceNow incident state sync) as read-only mirror.
- Formal state machine verification and model checking in CI for transition integrity.

## Example Workflow

**Scenario:** VP-CUBE-0001 investigation.

1. `NEW` → `INTAKE`: Case created with outbound failure symptom.
2. `INTAKE` → `DISCOVERY`: Intake questions answered; all outbound failing.
3. `DISCOVERY` → `TOPOLOGY`: CUCM → CUBE → ITSP path identified.
4. `TOPOLOGY` → `COLLECTION`: Topology validated; dial-peer and trunk elements modeled.
5. `COLLECTION` → `ANALYSIS`: Mandatory CLI and debug evidence collected.
6. `ANALYSIS` → `HYPOTHESIS`: Local 404 signal extracted; hypotheses generated.
7. `HYPOTHESIS` → `INVESTIGATION`: Dial-peer mismatch leading; discrimination in progress.
8. `INVESTIGATION` → `COLLECTION`: Rollback to collect dial-peer config (allowed).
9. `COLLECTION` → `ANALYSIS` → `HYPOTHESIS` → `INVESTIGATION`: Re-entry after new evidence.
10. `INVESTIGATION` → `RESOLUTION`: Confidence gate PASS at 92.
11. `RESOLUTION` → `VERIFICATION`: Fix applied; verification checklist initiated.
12. `VERIFICATION` → `LEARNING`: All tests passed.
13. `LEARNING` → `CLOSED`: Structured learning captured; report generated.
