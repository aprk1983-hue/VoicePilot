# Investigation Engine

## Purpose

The Investigation Engine is the orchestration core of VoicePilot. It owns the lifecycle of every incident investigation from case opening through verified resolution and structured closure. It does not behave like a conversational assistant; it behaves like a senior Cisco TAC engineer running a disciplined investigation with explicit state, evidence requirements, and decision gates.

The Investigation Engine is the only component authorized to advance investigation lifecycle state, mutate the canonical Case State, and declare investigation outcomes.

## Responsibilities

- Open and register new investigation cases with unique identity and audit lineage.
- Maintain the Case State as the single source of truth for every active and closed investigation.
- Coordinate intake, topology capture, evidence collection, hypothesis management, and resolution workflows.
- Delegate specialized work to domain engines while retaining accountability for outcomes.
- Request intelligent questions from the Question Engine based on current investigation context.
- Request evidence collection actions from the Evidence Engine when gaps are identified.
- Invoke the Reasoning Engine to generate, rank, and eliminate hypotheses.
- Invoke the Confidence Engine before any root cause confirmation or case closure gate.
- Select and apply playbooks via the Playbook Engine; permit controlled playbook switching.
- Confirm root cause only when evidence and confidence thresholds are satisfied.
- Drive verification and learning handoff before case closure.
- Emit structured investigation events for audit, reporting, and organizational learning.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case Intake | Engineer / Integration | Symptom, severity, business impact, affected scope, initial timeline |
| Case State Mutations | Subordinate Engines | Evidence additions, hypothesis updates, topology revisions, confidence changes |
| Lifecycle Transitions | State Machine | Validated state advance or rollback requests |
| Playbook Context | Playbook Engine | Active playbook, step position, branching decisions |
| Next Best Action | Reasoning Engine | Ranked investigative actions with rationale |
| Confidence Assessment | Confidence Engine | Score, explanation, threshold pass/fail |
| Knowledge Retrieval | Knowledge Engine | Facts, rules, CLI guidance, known bugs, compatibility constraints |
| Engineer Responses | Human Operator | Answers to TAC-style questions, command output, configuration excerpts |
| Verification Results | Engineer / Automation | Post-resolution test outcomes |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Canonical Case State | All Engines, Report Engine | Authoritative investigation record |
| Investigation Directives | Question Engine, Evidence Engine | What to ask, what to collect next |
| Lifecycle Events | State Machine, Audit, Report Engine | State transitions, gate results, timestamps |
| Next Best Action | Engineer Interface | Single prioritized investigative step |
| Root Cause Declaration | Report Engine, Learning Engine | Evidence-backed conclusion with confidence |
| Resolution Package | Report Engine | Resolution steps, verification plan, preventive actions |
| Closure Record | Learning Engine, Audit | Final case artifact with lessons learned |

## Internal State

The Investigation Engine maintains orchestration state separate from but synchronized with Case State:

- **Active Case Registry** — mapping of `case_id` to orchestration handles, owner, and session context.
- **Engine Coordination Context** — pending delegations, in-flight evidence requests, unanswered questions.
- **Playbook Binding** — active playbook identifier, version, current phase alignment with lifecycle state.
- **Gate Status** — intake complete, topology validated, minimum evidence satisfied, confidence threshold met, verification passed.
- **Decision Log** — chronological record of orchestration decisions with engine inputs and rationale references.
- **Concurrency Controls** — locks on Case State mutation to prevent conflicting updates during parallel evidence ingestion.

Case State fields owned or coordinated by this engine include: `case_id`, `status`, `severity`, `business_impact`, `symptom`, `affected_scope`, `platform`, `topology`, `timeline`, `recent_changes`, `known_facts`, `missing_evidence`, `evidence`, `hypotheses`, `confidence`, `next_best_action`, `root_cause`, `resolution`, `verification`, `preventive_action`, `lessons_learned`.

## Interactions

```
Engineer ──► Investigation Engine ◄──► State Machine
                    │
    ┌───────────────┼───────────────┬───────────────┐
    ▼               ▼               ▼               ▼
Question       Evidence        Reasoning      Confidence
Engine         Engine          Engine         Engine
    │               │               │               │
    └───────────────┼───────────────┴───────────────┘
                    ▼
            Playbook Engine
            Knowledge Engine
            Topology Engine
                    │
                    ▼
            Report Engine ──► Learning Engine (on closure)
```

- **State Machine** — Investigation Engine requests transitions; State Machine validates and commits lifecycle changes.
- **Question Engine** — Investigation Engine provides case context; receives ranked questions for presentation.
- **Evidence Engine** — Investigation Engine issues collection requirements; receives parsed evidence artifacts.
- **Reasoning Engine** — Investigation Engine supplies facts and evidence; receives hypothesis graph and next actions.
- **Confidence Engine** — Investigation Engine requests scoring at every major gate; blocks premature conclusions.
- **Playbook Engine** — Investigation Engine selects playbook at intake; rebinds on scope or vendor change.
- **Knowledge Engine** — Investigation Engine queries for rules, commands, and domain facts during each phase.
- **Topology Engine** — Investigation Engine requests topology model construction and validation.
- **Report Engine** — Investigation Engine triggers report generation at resolution and closure milestones.
- **Learning Engine** — Investigation Engine submits structured closure package after verification.

## Future Extensions

- Multi-case correlation for widespread outages affecting shared infrastructure.
- Investigation delegation and handoff between engineers with preserved state continuity.
- Automated evidence collection via device connectors (read-only CLI, CDR, syslog ingestion).
- Priority queuing and SLA enforcement based on severity and business impact.
- Investigation templates for recurring incident classes beyond playbook scope.
- Federated investigations spanning multiple tenants or managed service provider contexts.
- Real-time collaboration with conflict-free replicated Case State for distributed teams.

## Example Workflow

**Scenario:** VP-CUBE-0001 — Outbound PSTN calls fail. Topology: Cisco CUCM → Cisco CUBE → ITSP.

1. **Case Open** — Engineer reports outbound PSTN failure. Investigation Engine creates `case_id`, sets status `NEW`, records symptom and business impact, initializes empty evidence and hypothesis structures.

2. **Intake** — State advances to `INTAKE`. Investigation Engine binds Playbook Engine to `VP-CUBE-0001`. Question Engine returns highest-value intake questions: "Did this ever work?", "Recent changes?", "All outbound or selective?". Answers populate `known_facts` and `timeline`.

3. **Topology** — State advances to `TOPOLOGY`. Topology Engine models CUCM, CUBE, ITSP path. Investigation Engine validates dial-peer and SIP trunk elements are represented. Gaps trigger targeted topology questions.

4. **Collection** — State advances to `COLLECTION`. Evidence Engine identifies required commands: `show dial-peer voice summary`, `show sip-ua status`, `debug ccsip messages`. Engineer submits output. Evidence Engine scores quality and updates `evidence` and `missing_evidence`.

5. **Analysis & Hypothesis** — Reasoning Engine generates hypotheses: dial-peer mismatch, provider rejection, codec mismatch, firewall timeout. Each hypothesis links to supporting or contradicting evidence. Impossible hypotheses are removed with documented rationale.

6. **Investigation Loop** — Investigation Engine presents next best action: "Collect `show run | sec dial-peer` and compare called-number pattern to failing destination." Confidence Engine scores current hypothesis set. Loop continues until confidence threshold is met or new evidence forces re-ranking.

7. **Resolution** — Root cause confirmed: outbound dial-peer pattern excludes mobile number range. Confidence Engine passes gate. Investigation Engine records `root_cause` and `resolution` with evidence references.

8. **Verification** — Engineer executes verification steps from playbook: test local, mobile, and international outbound. Results recorded. State advances to `VERIFICATION`.

9. **Learning & Closure** — Learning Engine receives structured closure package. Report Engine generates technical and executive summaries. State advances to `CLOSED`.
