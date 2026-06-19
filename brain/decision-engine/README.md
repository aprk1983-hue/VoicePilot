# Decision Engine

## Purpose

The Decision Engine is the immutable audit ledger of every important technical decision made during a VoicePilot investigation. Senior TAC engineers document not only *what* they concluded, but *why*, *with what evidence*, and *what alternatives they rejected*. This engine makes that discipline structural and mandatory.

VoicePilot does not present conclusions as opinions. Every elimination, confirmation, strategy choice, and gate passage is a recorded decision with provenance.

## Responsibilities

- Record every significant technical decision with full attribution metadata.
- Capture decision text, rationale, supporting evidence, and confidence at time of decision.
- Document alternatives considered and explicit rejection reasons for each alternative.
- Timestamp and sequence decisions within the investigation timeline.
- Link decisions to hypotheses, evidence artifacts, strategies, and state transitions.
- Support engineer review and challenge of prior decisions with supersession records.
- Provide decision narratives for Report Engine RCA and elimination sections.
- Enforce minimum decision quality: no decision without reason and evidence reference.
- Distinguish decision types: elimination, confirmation, strategy, gate, escalation, waiver.
- Never auto-approve decisions that bypass evidence requirements.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Decision Events | All Brain Engines | Eliminations, confirmations, strategy changes, gate results |
| Evidence References | Evidence Engine | Artifact IDs supporting the decision |
| Hypothesis Context | Reasoning Engine | Hypothesis affected by decision |
| Confidence Snapshot | Confidence Engine | Score at decision time |
| Alternative Set | Reasoning Engine, Investigation Planner | Competing options considered |
| Engineer Attribution | Investigation Engine | Human-initiated vs. engine-recommended decisions |
| Strategy Context | Investigation Planner | Active strategy when decision made |
| State Context | State Machine | Lifecycle phase at decision time |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Decision Records | Case State, Investigation Graph | Structured decision entries |
| Decision Sequence | Timeline Engine | Ordered decision events |
| Elimination Narrative | Report Engine | Why each hypothesis was ruled out |
| Confirmation Record | Report Engine, Confidence Engine | Root cause confirmation decision package |
| Audit Trail | Compliance, Learning Engine | Immutable decision history |
| Challenge Response | Investigation Engine | Prior decision context when engineer disputes |
| Supersession Notices | Reasoning Engine | When new evidence overturns prior decision |

## Internal State

- **Decision Registry** — append-only log of all decisions per `case_id`.
- **Decision Type Index** — decisions grouped by: elimination, confirmation, strategy, gate, waiver, escalation.
- **Evidence Link Table** — bidirectional mapping between decisions and evidence artifacts.
- **Alternative Archive** — rejected options stored per decision with rejection rationale.
- **Supersession Chain** — links overturned decisions to superseding decisions.
- **Quality Validator** — rules enforcing mandatory fields before decision commit.
- **Sequence Counter** — monotonic decision ordering per case.

### Decision Record Structure

```yaml
decision_id:
case_id:
sequence:
type:                 # elimination | confirmation | strategy | gate | waiver | escalation
decision:             # concise statement of what was decided
reason:               # why this decision was made
evidence_used:        # list of evidence_id references
confidence:           # confidence at decision time (0-100)
timestamp:
actor:                # engine identity or engineer identity
alternatives_considered:
  - alternative:
    rejection_reason:
state_at_decision:
strategy_at_decision:
hypothesis_affected:
supersedes:           # prior decision_id if applicable
superseded_by:
engineer_acknowledged:  # true when engineer explicitly approved
```

### Example Decision Record

```yaml
decision_id: DEC-0007
case_id: CASE-1042
sequence: 7
type: elimination
decision: Eliminate DNS issue as root cause
reason: Provider FQDN resolved successfully to expected carrier SBC address
evidence_used: [E-004]
confidence: 94
timestamp: 2026-06-19T10:22:00Z
actor: reasoning-engine
alternatives_considered:
  - alternative: DNS resolution failure causing SIP timeout
    rejection_reason: nslookup and CUBE DNS cache show correct A-record; 404 returned not 408
state_at_decision: INVESTIGATION
strategy_at_decision: routing-first
hypothesis_affected: HYP-DNS-001
engineer_acknowledged: true
```

## Interactions With Other Engines

- **Reasoning Engine** — primary producer of elimination and confirmation decisions.
- **Investigation Planner** — records strategy selection and switch decisions.
- **Confidence Engine** — records gate pass/fail decisions with threshold context.
- **Evidence Engine** — supplies evidence IDs; records waiver decisions for missing evidence.
- **Investigation Engine** — commits decisions to Case State; handles engineer challenge flow.
- **Timeline Engine** — receives decision events for chronological placement.
- **Investigation Graph** — decision nodes linked to evidence and hypotheses via edges.
- **Report Engine** — consumes decision sequence for RCA and elimination narrative.
- **Learning Engine** — anonymized decision patterns indexed for institutional knowledge.
- **State Machine** — gate decisions referenced in transition authorization.

## MVP Workflow for VP-CUBE-0001: Outbound Calls Fail

1. **DEC-001 — Strategy Selection** — Investigation Planner decides Routing-first strategy. Alternatives: Provider-first (rejected — no carrier-wide symptoms), Network-first (rejected — no timeout pattern). Confidence: 78. Engineer acknowledged.

2. **DEC-002 — Eliminate SIP Trunk Down** — Reasoning Engine eliminates hypothesis. Reason: `show sip-ua status` shows all peers UP. Evidence: E-001. Confidence: 96.

3. **DEC-003 — Eliminate Provider Rejection** — Reason: SIP debug shows 404 generated locally on CUBE, not from ITSP. Evidence: E-002. Confidence: 91. Alternative considered: carrier routing rejection (rejected — response origin is local).

4. **DEC-004 — Elevate Dial-Peer Mismatch** — Reason: local 404 + outbound-only symptom matches routing-first proof objective. Evidence: E-002. Confidence: 72. Hypothesis: HYP-DP-001.

5. **DEC-005 — Waive International Test** — Engineer waives international verification (not in scope). Reason: domestic and mobile failures only. Type: waiver. Engineer acknowledged.

6. **DEC-006 — Confirm Root Cause** — Decision: dial-peer gap for mobile prefix range. Evidence: E-002, E-005. Confidence: 92. Gate pass from Confidence Engine. Alternatives: translation rule error (rejected — pattern analysis shows missing peer, not mistranslation).

7. **DEC-007 — Verification Pass** — Decision: resolution verified. Evidence: E-006, E-007 (post-fix test results). Confidence: 95.

All decisions flow to Timeline Engine and Investigation Graph. Report Engine includes elimination narrative from DEC-002 through DEC-004.

## Future Extensions

- Decision review workflow: second engineer sign-off for high-severity cases.
- Decision quality scoring: flag decisions with weak evidence linkage.
- Cross-case decision pattern analysis for training materials (not LLM training).
- Regulatory audit export with immutable hash chain.
- Decision templates per playbook for consistent elimination documentation.
- Natural language decision challenge: engineer asks "why was X eliminated?" — engine returns decision record.
- Integration with ITSM change records linked to change-correlation decisions.

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Decision without evidence | False audit trail, unsupported eliminations | Quality validator blocks commit; minimum one evidence ref for eliminations |
| Missing alternatives | Incomplete reasoning record | Reasoning Engine must supply at least one rejected alternative for eliminations |
| Silent supersession | Prior decision appears valid when overturned | Supersession chain mandatory; UI shows overturned status |
| Duplicate decisions | Inflated audit log, confusion | Idempotency key on decision events from source engines |
| Engineer bypass | Engine decisions without acknowledgment on critical gates | Critical decision types require `engineer_acknowledged: true` |
| Stale confidence | Decision cites outdated confidence | Confidence snapshot captured at decision timestamp, not current |

## Design Principles

1. **Every conclusion is a decision** — Root cause confirmation is a decision record, not a chat message.
2. **Alternatives are mandatory** — Elimination without considered alternatives fails validation.
3. **Evidence linkage required** — No evidence reference, no elimination decision committed.
4. **Append-only ledger** — Decisions are never deleted; supersession creates new records.
5. **Engineer in control** — Critical decisions require explicit engineer acknowledgment.
6. **Never guess** — Decisions document proof, not speculation; low-confidence decisions are flagged.
7. **State maintained** — Decision registry is part of Case State, persistent across sessions.
8. **Transparency over brevity** — Rejection reasons must be specific enough for third-party audit.
