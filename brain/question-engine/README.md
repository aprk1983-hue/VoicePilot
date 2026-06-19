# Question Engine

## Purpose

The Question Engine generates TAC-style investigative questions for VoicePilot. It never asks random or conversational questions. Every question is calculated to maximize investigation value: reducing uncertainty, collecting discriminating facts, filling topology gaps, or satisfying playbook intake requirements. The engine behaves like a senior engineer who asks exactly the question that moves the investigation forward.

## Responsibilities

- Generate contextually appropriate questions for each investigation phase.
- Rank unanswered questions by expected information gain.
- Select the single highest-value question for presentation at any moment.
- Suppress redundant, already-answered, or low-value questions.
- Align questions with active playbook, topology gaps, and hypothesis discrimination needs.
- Format questions with TAC professionalism: precise, actionable, free of ambiguity.
- Track question history: asked, answered, deferred, waived.
- Convert engineer answers into structured updates for Case State.
- Collaborate with Reasoning Engine to identify discriminating questions between competing hypotheses.
- Never ask questions whose answers cannot change the investigation outcome.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case State | Investigation Engine | Known facts, symptom, timeline, topology, hypotheses |
| Unanswered Question Registry | Internal | Prior questions not yet answered |
| Playbook Question Bank | Playbook Engine | Scenario-specific intake and phase questions |
| Topology Gaps | Topology Engine | Missing components, relationships, or configuration bindings |
| Hypothesis Discrimination Map | Reasoning Engine | Facts needed to separate top hypotheses |
| Missing Evidence Context | Evidence Engine | Information obtainable via question vs. CLI |
| Knowledge Prompts | Knowledge Engine | Domain-specific clarifiers and escalation triggers |
| Lifecycle State | State Machine | Phase-appropriate question categories |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Next Question | Investigation Engine | Single highest-value question with rationale |
| Question Queue | Investigation Engine | Ranked backlog for batch or deferred asking |
| Structured Answer Mapping | Case State | Field updates from engineer responses |
| Question History | Report Engine | Record of questions asked and answers received |
| Information Gain Score | Internal Audit | Per-question value calculation trace |
| Waived Question Record | Investigation Engine | Questions skipped with engineer rationale |

## Internal State

- **Question Registry** — all questions for active case with status and metadata.
- **Information Gain Model** — scoring weights: uncertainty reduction, hypothesis discrimination, topology completion, playbook compliance.
- **Answer Extraction Rules** — mapping from natural language answers to structured Case State fields.
- **Suppression Rules** — conditions under which questions are not asked (already known, irrelevant, out of phase).
- **Phase Filter** — which question categories are valid per lifecycle state.
- **Deferred Queue** — lower-priority questions held until higher-value options exhausted.

### Question Record Structure

```yaml
question_id:
case_id:
text:
category:         # intake | topology | scope | change | discrimination | verification
phase:
source:           # playbook | topology_gap | reasoning | knowledge
target_fields: [] # Case State fields this answer populates
information_gain_score:
hypotheses_affected: []
status:           # pending | asked | answered | deferred | waived
asked_at:
answered_at:
answer_structured:
```

### Information Gain Calculation

| Factor | Description |
|--------|-------------|
| Uncertainty Reduction | Expected reduction in hypothesis entropy |
| Discrimination Power | Ability to confirm/deny top two hypotheses |
| Topology Completion | Fills critical model gap blocking collection |
| Playbook Compliance | Required intake element not yet satisfied |
| Collection Efficiency | Answer may eliminate need for expensive debug |
| Phase Appropriateness | Penalty for out-of-phase questions |

**Selection rule:** Present the unanswered question with highest composite information gain score. Tie-break by playbook requirement priority, then collection efficiency.

## Interactions

- **Investigation Engine** — requests next question; submits answers for structuring.
- **Playbook Engine** — supplies scenario question banks and required intake elements.
- **Reasoning Engine** — supplies discrimination map; receives answers that update facts.
- **Topology Engine** — supplies topology gap questions; receives answers that populate topology model.
- **Evidence Engine** — coordinates when question answer triggers collection vs. when collection replaces question.
- **Knowledge Engine** — domain-specific question templates and clarifiers.
- **Confidence Engine** — certain questions required before confidence gates (e.g., recent changes).
- **State Machine** — phase constraints on question categories.

## Future Extensions

- Adaptive questioning based on engineer expertise level (junior vs. senior).
- Multi-select and structured form questions for complex topology capture.
- Question bundles for efficient intake (related questions grouped when gain is similar).
- Localization and regional regulatory question packs.
- Voice-to-structured-answer parsing with engineer confirmation gate.
- Question effectiveness analytics from Learning Engine closure data.
- Integration with ITSM for automatic change record correlation questions.

## Example Workflow

**Scenario:** VP-CUBE-0001 outbound failure, state `INTAKE`.

1. **Initialization** — Playbook Engine supplies intake questions. Question Engine registers 8 questions, all `pending`.

2. **First Selection** — Scoring: "Did outbound PSTN ever work in this environment?" scores highest (establishes baseline, affects hypothesis priors). Presented to engineer.

3. **Answer Structuring** — Engineer answers "Yes, worked until yesterday." Mapped to `known_facts.worked_previously: true`, `timeline.onset: yesterday`. Question marked `answered`.

4. **Second Selection** — "Were any changes made to CUBE, CUCM, or provider in the last 48 hours?" scores highest (change correlation). Answer: "CUBE dial-peer edit yesterday afternoon." Mapped to `recent_changes` and `timeline`.

5. **Phase Transition** — State advances to `DISCOVERY`. Question Engine activates discrimination and scope questions. Suppresses remaining pure intake questions already satisfied.

6. **Topology Phase** — Topology Engine reports gap: ITSP provider identity unknown. Question: "Which ITSP/SIP provider carries outbound PSTN for this site?" High topology completion score. Answer populates topology model.

7. **Investigation Phase** — Reasoning Engine requests discrimination: "Are failing calls only to mobile numbers, or also landline?" Scores above generic questions. Answer eliminates broad provider outage hypothesis.

8. **Suppression** — Question Engine suppresses "Are inbound calls working?" — already answered in intake. Prevents redundant asking.

9. **Report** — Question history exported: 12 questions asked, 2 deferred, 1 waived ("International not in scope").
