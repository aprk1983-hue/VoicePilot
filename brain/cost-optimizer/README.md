# Cost Optimizer

## Purpose

The Cost Optimizer prioritizes the most valuable next investigative action by balancing expected information gain against operational cost and risk. A senior TAC engineer does not start with packet captures and gateway restarts — they ask a targeted question or run a show command first. This engine ensures VoicePilot recommends low-risk, high-information actions before expensive or disruptive ones.

The Cost Optimizer does not execute actions. It ranks them. The engineer remains in control of every action taken.

## Responsibilities

- Assign operational cost and risk levels to every candidate investigative action.
- Calculate expected information gain for each action given current case context.
- Produce a ranked action list optimized for value-per-cost ratio.
- Recommend the single best next action to Investigation Planner and Investigation Engine.
- Flag actions that exceed organizational risk tolerance without engineer approval.
- Support cost model customization per customer, severity, and maintenance window.
- Re-rank actions dynamically as evidence, hypotheses, and graph state change.
- Block recommendation of disruptive actions when equivalent low-cost alternatives exist.
- Document cost rationale for audit and engineer transparency.
- Coordinate with Question Engine and Evidence Engine on action type classification.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Candidate Actions | Reasoning, Question, Evidence, Investigation Planner | Questions, CLI commands, debug, captures, config changes |
| Information Gain Estimates | Question Engine, Reasoning Engine | Expected uncertainty reduction per action |
| Hypothesis Discrimination Map | Reasoning Engine | Which actions discriminate top hypotheses |
| Evidence Gaps | Evidence Engine | Missing artifacts and their collection cost |
| Topology Context | Topology Engine | Target devices and access requirements |
| Case Severity | Investigation Engine | May adjust risk tolerance thresholds |
| Active Strategy | Investigation Planner | Strategy-specific action prioritization |
| Graph Gaps | Investigation Graph | Nodes requiring edges; high-value collection targets |
| Risk Policy | Configuration | Organizational cost ceiling per phase |
| Engineer Constraints | Human Operator | "No debug on production" type directives |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Ranked Action List | Investigation Planner, Investigation Engine | Actions sorted by value-per-cost |
| Recommended Next Action | Investigation Engine | Single top action with cost and gain scores |
| Risk Flags | Investigation Engine | Actions requiring engineer approval |
| Cost Rationale | Decision Engine, Report Engine | Why an action was or was not recommended |
| Deferred Actions | Internal | High-cost actions held until justified |
| Approval Requests | Engineer Interface | Critical/Critical-risk actions pending acknowledgment |

## Internal State

- **Cost Model Registry** — action type to cost level mapping with override rules.
- **Candidate Action Queue** — all pending actions with scores per case.
- **Ranking Cache** — last computed ranking with context hash for invalidation.
- **Risk Policy Store** — per-severity and per-customer risk ceilings.
- **Approval Tracker** — critical actions awaiting engineer acknowledgment.
- **Deferral Registry** — high-cost actions deferred with justification requirements.
- **Score History** — how action rankings changed as investigation progressed.

### Operational Cost Levels

| Cost Level | Risk Profile | Example Actions |
|------------|--------------|-----------------|
| Low | Read-only, non-disruptive | Ask engineer a question; run `show` command; review existing logs |
| Medium | Read-only but resource-intensive | Enable debug logging; collect large log excerpts; run test calls |
| High | Potentially disruptive to operations | Packet capture on production path; extended debug during business hours |
| Critical | Service-impacting or irreversible | Restart gateway; production configuration change; failover trigger |

### Ranking Formula (Conceptual)

```
action_score = (information_gain × discrimination_weight × strategy_alignment)
               ─────────────────────────────────────────────────────────────
                            operational_cost_multiplier
```

Where `operational_cost_multiplier` maps: Low=1, Medium=3, High=8, Critical=25.

Actions below a minimum information gain threshold are suppressed regardless of low cost.

## Interactions With Other Engines

- **Investigation Planner** — primary consumer of ranked actions for dispatch planning.
- **Investigation Engine** — presents recommended action to engineer; enforces approval gates.
- **Question Engine** — supplies question-type actions with information gain scores.
- **Evidence Engine** — supplies collection actions with cost classification.
- **Reasoning Engine** — supplies discrimination value per action for top hypotheses.
- **Investigation Graph** — graph gaps inform collection priority.
- **Decision Engine** — records when high-cost action was approved or rejected.
- **Timeline Engine** — logs action recommendations and approval events.
- **Confidence Engine** — may boost priority of actions needed for gate passage.
- **Knowledge Engine** — command cost classifications and risk advisories per platform.

## MVP Workflow for VP-CUBE-0001: Outbound Calls Fail

**Candidate actions after intake (Routing-first strategy):**

| Action | Cost | Info Gain | Score Rank |
|--------|------|-----------|------------|
| Ask: "All outbound or mobile only?" | Low | High | **1** |
| Ask: "Recent changes?" | Low | High | **2** |
| `show sip-ua status` | Low | High | **3** |
| `show dial-peer voice summary` | Low | High | **4** |
| `debug ccsip messages` (single call) | Medium | High | **5** |
| `show run | sec dial-peer` | Low | Medium | **6** |
| Packet capture on CUBE WAN interface | High | Medium | Deferred |
| Restart CUBE SIP-UA | Critical | Low | Blocked — low gain, high risk |

**Recommendation sequence:**

1. **Rank 1** — Question: failure scope. Cost Optimizer recommends first. Engineer answers: mobile only.

2. **Rank 3** — `show sip-ua status`. Proves trunk registration. Eliminates low-cost hypothesis.

3. **Rank 5** — `debug ccsip messages`. Medium cost justified by high discrimination (local vs. provider 404). Engineer approves debug.

4. **After local 404 found** — `show run | sec dial-peer` rises to Rank 1 (high discrimination, low cost).

5. **Deferred** — Packet capture not recommended; sufficient evidence available via CLI and debug.

6. **Blocked** — Restart CUBE not recommended; no evidence supports SIP stack failure.

7. **Post-fix** — Test call (Low cost) recommended before any configuration rollback consideration.

## Future Extensions

- Customer-specific cost models (lab vs. production environment profiles).
- Maintenance window awareness: Critical actions only recommended inside approved windows.
- Automated cost estimation based on device load and time of day.
- Action bundling: group low-cost actions for single engineer interaction.
- Cost vs. time tradeoff: prefer faster resolution actions when SLA breach imminent.
- Integration with change management for Critical action pre-approval workflows.
- Historical cost effectiveness: which action types resolved similar cases fastest.
- Engineer expertise adjustment: fewer questions for senior engineers, more for junior.

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| High-cost action ranked first | Engineer distrust, operational risk | Cost multiplier heavily penalizes High/Critical; suppression rules |
| Zero information gain actions | Wasted engineer time | Minimum gain threshold filters low-value actions |
| Ignoring engineer constraints | Recommends blocked action types | Engineer directives override ranking; constraints cached per case |
| Stale ranking | Wrong action after new evidence | Context hash invalidation on evidence/hypothesis/graph change |
| Over-deferral | Investigation stall avoiding medium-cost actions | Stall detector escalates medium-cost actions after N cycles |
| False low-cost classification | Debug during peak misclassified as Low | Knowledge Engine provides platform-specific cost classifications |

## Design Principles

1. **Low risk first** — Default recommendation order favors questions and show commands.
2. **Information gain drives rank** — Cost is denominator, not the primary sort key.
3. **Never guess** — Cost Optimizer ranks actions to *obtain* evidence, not to infer conclusions.
4. **Engineer in control** — Critical actions require explicit approval; recommendations are not commands.
5. **State maintained** — Ranking history and approval status persist in case state.
6. **Disruptive actions last** — Restart and production config change are never first recommendation.
7. **Transparent rationale** — Every recommendation includes cost level and expected gain.
8. **Equivalent alternative check** — Do not recommend High/Critical when Low action provides same discrimination.
