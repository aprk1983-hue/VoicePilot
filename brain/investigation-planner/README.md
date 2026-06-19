# Investigation Planner

## Purpose

The Investigation Planner is the strategic controller of every VoicePilot investigation. While the Investigation Engine orchestrates execution and owns Case State, the Investigation Planner decides *how* the investigation should proceed: which strategy to apply, what to prove first, when to change direction, which engine should act next, when sufficient evidence has been collected, and when the case may advance toward resolution.

This engine embodies the senior TAC engineer's instinct to choose an investigation path before collecting random diagnostics. It does not chat. It plans.

## Responsibilities

- Select and bind an investigation strategy based on symptom, topology, playbook, and early evidence.
- Define proof objectives: what must be established before advancing phase or confirming root cause.
- Decide which engine acts next: Question, Evidence, Reasoning, Topology, or Confidence.
- Detect when the current strategy is failing and recommend a controlled direction change.
- Evaluate evidence sufficiency against strategy-specific completion criteria.
- Align strategy with active playbook phase and State Machine lifecycle position.
- Authorize progression toward resolution only when strategy objectives are met.
- Maintain strategy history: initial selection, switches, and rationale for each change.
- Defer to the engineer for approval on strategy changes that increase operational risk.
- Coordinate with Cost Optimizer to ensure planned actions are high-value and low-risk first.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case State Snapshot | Investigation Engine | Symptom, scope, phase, facts, evidence, hypotheses |
| Active Playbook | Playbook Engine | Scenario guidance and phase requirements |
| Topology Model | Topology Engine | Call path, components, completeness |
| Strategy Catalog | Knowledge Engine | Strategy definitions, applicability rules, proof objectives |
| Hypothesis Status | Reasoning Engine | Active, leading, and eliminated hypotheses |
| Evidence Coverage | Evidence Engine | Collected vs. required artifacts per strategy |
| Confidence Assessment | Confidence Engine | Current score and gate proximity |
| Cost-Ranked Actions | Cost Optimizer | Next actions with information gain and operational cost |
| Engineer Directive | Human Operator | Strategy override, approval, or deferral |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Active Strategy | Investigation Engine, Case State | Current strategy ID and binding timestamp |
| Proof Objectives | Reasoning, Evidence Engines | What must be proven next |
| Next Engine Directive | Investigation Engine | Which engine to invoke and with what intent |
| Strategy Switch Recommendation | Investigation Engine | Proposed new strategy with rationale |
| Evidence Sufficiency Verdict | State Machine, Investigation Engine | Sufficient / insufficient for phase advance |
| Resolution Readiness | Investigation Engine, Confidence Engine | Whether strategy objectives support closure path |
| Strategy History | Decision Engine, Timeline Engine | Record of strategy selections and changes |
| Stall Detection | Investigation Engine | No progress signal with recommended pivot |

## Internal State

- **Active Strategy Binding** — `case_id` → strategy ID, version, bind time, proof objective checklist.
- **Strategy Catalog Cache** — available strategies with applicability scores.
- **Proof Objective Tracker** — per-objective status: open, in progress, satisfied, waived.
- **Engine Dispatch Queue** — ordered list of planned engine invocations.
- **Strategy Switch History** — prior strategies, switch reasons, engineer approval status.
- **Stall Counter** — cycles without proof objective progress or hypothesis discrimination.
- **Sufficiency Ruleset** — strategy-specific evidence and confidence requirements.

### Supported Investigation Strategies

| Strategy | When Applied | Primary Proof Focus |
|----------|--------------|---------------------|
| Routing-first | Local SIP codes, dial-peer symptoms, pattern-specific failures | CUCM route patterns, CUBE dial-peers, translation rules |
| Provider-first | Provider-originated codes (503, 403), carrier-wide symptoms | SIP trunk registration, provider reachability, carrier status |
| Network-first | Timeouts (408), intermittent failures, multi-site impact | Firewall, DNS, routing, latency, packet loss |
| Media-first | 488, one-way audio, post-connect failures | Codec negotiation, SDP, RTP pinholes |
| Security-first | TLS failures, certificate errors, toll fraud indicators | Certificates, encryption policy, ACLs |
| Change-first | Recent change correlated with onset | Change window correlation, config diff, rollback validation |

## Interactions With Other Engines

- **Investigation Engine** — receives plan directives; submits strategy approval requests; executes planned engine sequence.
- **Playbook Engine** — playbook constrains default strategy; planner may override when evidence dictates.
- **Reasoning Engine** — receives proof objectives; informs planner when hypotheses require strategy pivot.
- **Evidence Engine** — reports coverage against strategy-specific requirements.
- **Question Engine** — invoked when planner prioritizes low-cost information gathering.
- **Topology Engine** — strategy selection uses topology pattern (e.g., CUBE in path → routing-first candidate).
- **Confidence Engine** — planner requests sufficiency check before authorizing resolution path.
- **Cost Optimizer** — planner consumes cost-ranked actions when building dispatch queue.
- **Decision Engine** — records strategy selections and switches as formal decisions.
- **Timeline Engine** — receives strategy change events for chronological record.
- **Investigation Graph** — strategy nodes linked to proof objectives and evidence requirements.
- **State Machine** — planner cannot force transitions; recommends when gates may be satisfied.

## MVP Workflow for VP-CUBE-0001: Outbound Calls Fail

**Topology:** Cisco CUCM → Cisco CUBE → ITSP. Symptom: outbound PSTN failure.

1. **Strategy Selection** — Playbook `VP-CUBE-0001` bound. Symptom: outbound failure, platform CUBE. Planner scores strategies: Routing-first (0.85), Change-first (0.72 — recent dial-peer edit reported), Provider-first (0.45). **Routing-first** selected with Change-first as secondary lens.

2. **Proof Objectives Defined** — (a) Confirm CUBE is generating failure locally vs. provider. (b) Validate dial-peer match for failing destination class. (c) Rule out trunk registration failure.

3. **Engine Dispatch — Intake** — Planner directs Question Engine: confirm failure scope (all outbound vs. mobile-only) and recent changes. Low cost, high information gain.

4. **Engine Dispatch — Collection** — Planner directs Evidence Engine: `show sip-ua status` (prove trunk up), `debug ccsip messages` (prove 404 origin). Cost Optimizer confirms both are low-to-medium cost.

5. **Mid-Investigation Pivot** — Evidence shows local 404, trunk registered. Planner maintains Routing-first. Adds proof objective: dial-peer pattern gap for mobile prefixes. Directs Evidence Engine for `show run | sec dial-peer`.

6. **Sufficiency Check** — Dial-peer gap confirmed. Planner evaluates: routing proof objectives satisfied. Requests Confidence Engine gate before resolution path.

7. **Resolution Authorization** — Confidence gate pass. Planner authorizes Investigation Engine to advance toward `RESOLUTION`. Verification objectives handed to Playbook Engine checklist.

8. **Closure** — Strategy history recorded: Routing-first throughout, Change-first correlation noted. Timeline and Decision Engine updated.

## Future Extensions

- Multi-strategy parallel tracks for complex multi-vendor incidents.
- Machine-readable strategy effectiveness scoring from Learning Engine.
- Customer-specific strategy preferences and risk tolerance profiles.
- Automatic strategy simulation: projected cycles to resolution per strategy.
- Integration with maintenance windows for strategy actions involving production risk.
- Strategy templates per playbook with engineer-customizable proof objectives.
- Collaborative planning: senior engineer approves strategy for junior-led investigations.

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Wrong strategy selected | Delayed resolution, unnecessary evidence collection | Stall detection triggers strategy switch recommendation; engineer override always available |
| Premature sufficiency declaration | Root cause confirmed without adequate proof | Confidence Engine and Evidence Engine gates block; planner sufficiency is advisory only |
| Strategy oscillation | Rapid switching between strategies without progress | Oscillation detector limits switches per N cycles; escalate to engineer |
| Ignoring engineer override | Planner persists with rejected strategy | Engineer directive is authoritative; planner must rebind |
| Stale strategy after scope change | Plan misaligned with updated topology | Topology change event forces strategy re-evaluation |
| Over-planning before intake | Plan built on insufficient facts | Minimum intake gate before strategy binding beyond playbook default |

## Design Principles

1. **Strategy before action** — No engine dispatch without a stated proof objective.
2. **Engineer in control** — Strategy changes with operational risk require engineer approval.
3. **Evidence-driven pivots** — Strategy switches must cite evidence or stall detection, never intuition.
4. **Never guess** — Planner selects paths to *prove* hypotheses; it does not declare root cause.
5. **State maintained** — Strategy binding and history are part of investigation state, not session memory.
6. **Low cost first** — Default dispatch order respects Cost Optimizer ranking unless urgency overrides.
7. **Playbook-aligned, evidence-liberated** — Playbook suggests strategy; evidence may override.
8. **Auditable planning** — Every strategy decision flows to Decision Engine and Timeline Engine.
