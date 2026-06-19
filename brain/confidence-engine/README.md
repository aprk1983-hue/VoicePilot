# Confidence Engine

## Purpose

The Confidence Engine quantifies investigative certainty for VoicePilot. It produces explainable confidence scores, maintains confidence history, and enforces configurable thresholds that gate critical decisions — especially root cause confirmation and case closure. This engine ensures VoicePilot never presents a conclusion with false certainty.

A senior TAC engineer says "I'm confident because X, Y, and Z." This engine makes that discipline measurable and auditable.

## Responsibilities

- Calculate aggregate investigation confidence from evidence quality, hypothesis support, and knowledge alignment.
- Produce human-readable confidence explanations suitable for engineer review and executive reporting.
- Maintain confidence history and trend across the investigation lifecycle.
- Enforce configurable confidence thresholds for: hypothesis confirmation, root cause declaration, resolution acceptance, and case closure.
- Block root cause confirmation when confidence falls below threshold — without exception.
- Score per-hypothesis confidence contributions independently from case-level confidence.
- Detect confidence regression when new evidence contradicts prior conclusions.
- Emit confidence gate pass/fail results to Investigation Engine and State Machine.
- Support threshold policies per severity, playbook, and organizational risk tolerance.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Hypothesis Graph | Reasoning Engine | Ranked hypotheses with support/contradiction links |
| Evidence Quality Scores | Evidence Engine | Per-artifact and coverage metrics |
| Knowledge Requirements | Knowledge Engine | Minimum evidence standards per root cause class |
| Case Context | Investigation Engine | Severity, business impact, investigation phase |
| Threshold Policy | Configuration | Organizational gates per decision type |
| Topology Validation | Topology Engine | Completeness and consistency of topology model |
| Verification Results | Investigation Engine | Post-resolution test outcomes |
| Historical Baseline | Learning Engine | Typical confidence curves for similar closed cases |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Confidence Score | Case State, Investigation Engine | Current aggregate score (0–100 or normalized scale) |
| Confidence Explanation | Engineer Interface, Report Engine | Structured rationale: what raises and lowers confidence |
| Confidence History | Case State, Report Engine | Timestamped score snapshots with trigger events |
| Confidence Trend | Investigation Engine | Direction: rising, stable, falling, volatile |
| Gate Results | State Machine, Investigation Engine | PASS / FAIL / BLOCKED for each decision gate |
| Threshold Recommendations | Investigation Engine | Evidence or actions needed to reach next threshold |
| Per-Hypothesis Confidence | Reasoning Engine | Individual hypothesis certainty scores |
| Regression Alerts | Investigation Engine | Notification when new evidence undermines prior confidence |

## Internal State

- **Scoring Model Configuration** — weights for evidence quality, hypothesis discrimination, topology completeness, verification success.
- **Threshold Registry** — per-gate thresholds: `hypothesis_confirm`, `root_cause_declare`, `resolution_accept`, `case_close`.
- **Confidence Timeline** — append-only log of score calculations with input snapshot hashes.
- **Gate Evaluation Cache** — last gate results per decision type to avoid redundant computation.
- **Explanation Template Library** — patterns for generating consistent, auditable explanations.
- **Regression Detector State** — prior confirmed hypothesis confidence baseline for comparison.

### Confidence Composition Model

| Factor | Weight Domain | Description |
|--------|---------------|-------------|
| Evidence Coverage | 0–30% | Mandatory evidence collected vs. required |
| Evidence Quality | 0–25% | Aggregate quality scores from Evidence Engine |
| Hypothesis Discrimination | 0–25% | Leading hypothesis separation from alternatives |
| Topology Completeness | 0–10% | Validated topology model coverage |
| Knowledge Alignment | 0–10% | Conclusion matches known patterns and rules |
| Verification Success | Gate modifier | Required for closure; can block regardless of score |

**Hard gates (non-negotiable):**

- Root cause confirmation blocked if mandatory evidence missing.
- Root cause confirmation blocked if leading hypothesis has active contradicting evidence.
- Case closure blocked if verification incomplete or failed.
- Configurable minimum score for root cause declaration (default: 85).

## Interactions

- **Investigation Engine** — requests scoring at every major decision point; acts on gate results.
- **Reasoning Engine** — supplies hypothesis graph; receives per-hypothesis confidence updates.
- **Evidence Engine** — supplies quality and coverage metrics; receives threshold gap analysis.
- **State Machine** — confidence gate failure prevents transition to `RESOLUTION` or `CLOSED`.
- **Knowledge Engine** — provides minimum evidence standards and pattern match confidence boosts.
- **Topology Engine** — topology gaps reduce confidence and appear in explanation.
- **Report Engine** — receives confidence history and explanation for RCA and executive summary.
- **Learning Engine** — contributes baseline curves; receives final confidence metrics from closed cases.

## Future Extensions

- Organization-specific scoring models with audited weight configuration.
- Risk-adjusted thresholds: higher bar for high-severity or executive-escalated cases.
- Multi-stakeholder confidence: separate technical confidence vs. business resolution confidence.
- Confidence simulation: "what score would we reach if we collected artifact X?"
- Integration with change management: recent unverified changes lower confidence until ruled in/out.
- Formal uncertainty quantification with confidence intervals on hypothesis rankings.
- Regulatory audit mode with immutable confidence calculation reproducibility.

## Example Workflow

**Scenario:** Dial-peer mismatch hypothesis leading near root cause confirmation.

1. **Initial Score** — After intake only: confidence 12. Explanation: "Insufficient evidence. No CLI output collected. Three active competing hypotheses."

2. **Post-Collection Score** — After `show sip-ua status` and SIP debug: confidence 58, trend rising. Explanation: "Trunk registration confirmed. Local 404 origin supports dial-peer hypothesis. Missing dial-peer configuration. Two hypotheses eliminated."

3. **Gate Check — Root Cause** — Threshold 85. Result: FAIL. Investigation Engine receives: "Collect `show run | sec dial-peer` and confirm failing prefix match. Estimated confidence gain: +22."

4. **Post-Config Score** — Dial-peer config collected. Confidence 81. Explanation: "Mobile prefix uncovered in failing number range. No contradicting evidence. Verification tests not yet performed."

5. **Verification Gate** — Mobile outbound test passes after fix. Verification factor applied. Confidence 92. Trend: stable high.

6. **Root Cause Gate** — Threshold 85. Result: PASS. Investigation Engine authorized to record root cause.

7. **Closure Gate** — All verification steps from playbook complete. Closure threshold 80. Result: PASS. Confidence history exported to Report Engine and Learning Engine.
