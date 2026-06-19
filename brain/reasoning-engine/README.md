# Reasoning Engine

## Purpose

The Reasoning Engine performs evidence-constrained diagnostic reasoning for VoicePilot. It generates, ranks, updates, and eliminates hypotheses based on known facts and collected evidence. It never guesses. Every hypothesis must declare its supporting evidence, contradicting evidence, and knowledge references. When evidence is insufficient, the engine recommends collection actions — not conclusions.

This engine embodies the TAC principle: **form hypotheses early, eliminate aggressively, confirm only with proof.**

## Responsibilities

- Generate candidate root cause hypotheses from symptoms, topology, evidence, and knowledge rules.
- Rank hypotheses by evidential support, not by conversational plausibility.
- Update hypothesis confidence as new evidence arrives or is retracted.
- Eliminate hypotheses that are contradicted by evidence or ruled impossible by knowledge rules.
- Determine the next best investigative action to maximize information gain or confirm/deny top hypotheses.
- Maintain explicit hypothesis lineage: creation reason, evidence links, elimination reason.
- Refuse root cause confirmation requests when evidence or confidence gates are not satisfied.
- Distinguish between **primary root cause**, **contributing factors**, and **red herrings**.
- Surface uncertainty explicitly when multiple hypotheses remain viable.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case State Snapshot | Investigation Engine | `known_facts`, `evidence`, `topology`, `symptom`, `timeline`, `recent_changes` |
| Knowledge Facts | Knowledge Engine | Interpretation rules, root cause patterns, known bugs, configuration rules |
| Evidence Assessment | Evidence Engine | Quality scores, source reliability, parsed signal extractions |
| Active Playbook | Playbook Engine | Hypothesis templates, elimination criteria, investigation branches |
| Confidence Policy | Confidence Engine | Threshold requirements, scoring weights, gate definitions |
| Topology Model | Topology Engine | Component relationships, path validity, configuration bindings |
| Elimination Directives | Investigation Engine | Engineer-confirmed facts that rule out specific causes |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Hypothesis Graph | Investigation Engine, Case State | Ranked hypotheses with evidence links and status |
| Hypothesis Mutations | Investigation Engine | Create, update, rank, eliminate operations with rationale |
| Next Best Action | Investigation Engine, Question Engine | Single prioritized investigative step with expected information gain |
| Elimination Records | Evidence Engine, Report Engine | Documented reasons for ruled-out hypotheses |
| Uncertainty Declaration | Confidence Engine, Report Engine | Explicit statement when conclusion is premature |
| Collection Recommendations | Evidence Engine | Targeted evidence needed to discriminate between top hypotheses |

## Internal State

- **Hypothesis Registry** — all active, confirmed, and eliminated hypotheses per case.
- **Evidence Link Matrix** — bidirectional mapping between hypotheses and evidence artifacts (supports, contradicts, neutral).
- **Ranking Model State** — current scores, tie-breakers, and last recalculation timestamp.
- **Elimination Log** — immutable record of eliminated hypotheses with evidence and rule references.
- **Discrimination Map** — which evidence types would most effectively separate top competing hypotheses.
- **Reasoning Trace** — auditable decision path for every rank change and elimination (not exposed as chat).

### Hypothesis Record Structure

Each hypothesis carries:

- `hypothesis_id`, `title`, `description`
- `status`: candidate | active | confirmed | eliminated
- `supporting_evidence[]`, `contradicting_evidence[]`
- `knowledge_references[]`
- `affected_components[]` from topology
- `confidence_contribution` (input to Confidence Engine)
- `elimination_reason` (if eliminated)
- `created_at`, `last_updated`

## Interactions

- **Investigation Engine** — primary orchestrator; triggers reasoning cycles after evidence or fact changes.
- **Evidence Engine** — supplies parsed signals and quality scores; receives collection recommendations.
- **Knowledge Engine** — provides interpretation rules and pattern libraries that constrain hypothesis generation.
- **Confidence Engine** — consumes hypothesis scores; returns aggregate confidence and gate results.
- **Question Engine** — receives next best action when the action is a question; collaborates on information gain.
- **Playbook Engine** — supplies scenario-specific hypothesis seeds and branch logic.
- **Topology Engine** — provides path analysis: which components could plausibly cause observed symptoms.
- **Report Engine** — receives final hypothesis graph and elimination narrative for RCA section.

### Core Reasoning Rules

1. **No evidence, no hypothesis elevation** — hypotheses remain `candidate` until at least one supporting signal exists.
2. **Contradiction eliminates** — a single high-quality contradicting artifact eliminates a hypothesis unless overridden by investigation lead with documented rationale.
3. **Knowledge rules are hard constraints** — e.g., "TLS handshake failure cannot be caused by dial-peer pattern alone" eliminates incoherent combinations.
4. **Tie-breaking favors testability** — when hypotheses score equally, prefer the action that produces discriminating evidence fastest.
5. **Never fabricate missing proof** — if asked for root cause without sufficient evidence, output `INSUFFICIENT_EVIDENCE` and a collection plan.

## Future Extensions

- Bayesian belief network overlay for probabilistic ranking with explicit priors from knowledge corpus.
- Multi-root-cause investigations with dependency graphs (primary cause triggered secondary failure).
- Temporal reasoning across evidence timeline (change preceded symptom onset).
- Cross-case pattern matching from Learning Engine to seed hypotheses with historical priors.
- Vendor-specific reasoning modules pluggable without changing orchestration contract.
- Adversarial hypothesis testing: actively seek evidence that would disprove the leading hypothesis.

## Example Workflow

**Scenario:** Outbound calls fail with fast busy. CUCM → CUBE → ITSP.

1. **Initial Generation** — Reasoning Engine receives symptom and topology. Generates candidate hypotheses: dial-peer mismatch, SIP trunk down, provider rejection (503), codec mismatch (488), firewall timeout (408), DNS resolution failure.

2. **First Evidence Cycle** — Engineer provides `show sip-ua status`: trunk registered. Reasoning Engine eliminates "SIP trunk down." Elevates provider rejection and dial-peer mismatch.

3. **SIP Trace Evidence** — Evidence Engine parses `debug ccsip messages`: `404 Not Found` generated locally on CUBE before ITSP involvement. Knowledge rule: local 404 → routing/dial-peer issue. Reasoning Engine eliminates provider rejection, codec mismatch, firewall timeout for this symptom class. Dial-peer mismatch becomes leading hypothesis.

4. **Configuration Evidence** — `show run | sec dial-peer` shows pattern `9T` for domestic but no peer for mobile prefixes. Supporting evidence linked. Contradicting evidence: none. Hypothesis confidence contribution rises.

5. **Next Best Action** — Remaining discrimination needed: confirm failing calls match uncovered prefix range. Reasoning Engine outputs action: "Test call to known mobile number; capture CUBE dial-peer matched in `show call active voice brief`."

6. **Confirmation Gate** — Test confirms dial-peer 200 matched for mobile call with no valid destination. Reasoning Engine marks hypothesis `confirmed`. Investigation Engine requests Confidence Engine gate before recording root cause.

7. **Elimination Narrative** — Report Engine receives elimination log: trunk down ruled by registration status; provider issues ruled by local 404 origin.
