# Report Engine

## Purpose

The Report Engine produces enterprise-grade investigation deliverables from the canonical Case State and engine outputs. It transforms structured investigation data into incident summaries, root cause analyses, timelines, and executive communications suitable for technical teams, management, and post-incident review boards.

VoicePilot does not end with a chat transcript. It ends with a TAC-quality incident report.

## Responsibilities

- Generate incident summary documents at resolution and closure milestones.
- Produce root cause analysis with evidence citations and hypothesis elimination narrative.
- Construct investigation timelines from case events, evidence collection, and state transitions.
- Compile evidence appendices with artifact references and parsed signal summaries.
- Document recommendations and preventive actions from resolution and lessons learned.
- Record verification results with pass/fail status per playbook step.
- Generate executive summary: business impact, resolution status, risk posture.
- Generate technical summary: root cause, fix, evidence, configuration changes.
- Support multiple output formats for different audiences (same facts, different emphasis).
- Ensure report consistency: every claim traceable to Case State or evidence artifact.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Case State | Investigation Engine | Complete investigation record |
| State Transition History | State Machine | Lifecycle timeline |
| Evidence Registry | Evidence Engine | Artifacts, quality scores, parsed signals |
| Hypothesis Graph | Reasoning Engine | Confirmed root cause and elimination log |
| Confidence Record | Confidence Engine | Score, explanation, history |
| Topology Model | Topology Engine | Infrastructure diagram data (structured) |
| Question History | Question Engine | Intake and investigation Q&A |
| Playbook Record | Playbook Engine | Applied playbook, verification checklist |
| Verification Results | Investigation Engine | Test outcomes |
| Lessons Learned | Learning Engine | Structured post-incident knowledge |
| Report Templates | Knowledge Engine | Organizational report format standards |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Incident Summary | Engineer, ITSM | Complete incident overview |
| Root Cause Analysis | Engineering, Management | Evidence-backed RCA document |
| Investigation Timeline | All stakeholders | Chronological event sequence |
| Evidence Appendix | Engineering, Audit | Artifact index with summaries |
| Recommendations | Operations | Immediate and follow-up actions |
| Preventive Actions | Change Management | Changes to prevent recurrence |
| Verification Results | Operations, Audit | Test outcome documentation |
| Executive Summary | Leadership | Non-technical impact and resolution overview |
| Technical Summary | Engineering Teams | Detailed technical findings and fix |
| Closure Report | Learning Engine, Archive | Final immutable case document |

## Internal State

- **Report Template Registry** — organizational and scenario-specific templates.
- **Generation Pipeline State** — section assembly status per report instance.
- **Citation Index** — mapping from report claims to Case State fields and evidence IDs.
- **Report Version History** — draft and final versions with generation timestamps.
- **Audience Profile** — section inclusion rules per report type.
- **Export Format Registry** — supported output formats (structured document, not implementation-specific).

### Report Sections

| Section | Primary Sources |
|---------|-----------------|
| Incident Summary | Case State intake, symptom, impact, scope |
| Executive Summary | Business impact, resolution status, preventive headline |
| Technical Summary | Root cause, resolution, topology, evidence highlights |
| Root Cause Analysis | Reasoning Engine, Confidence Engine, Evidence Engine |
| Investigation Timeline | State Machine, Evidence timeline, Question history |
| Evidence Appendix | Evidence Engine registry |
| Hypothesis Elimination | Reasoning Engine elimination log |
| Topology Overview | Topology Engine model |
| Recommendations | Resolution, Knowledge Engine best practices |
| Preventive Actions | Case State, lessons learned |
| Verification Results | Playbook checklist, test outcomes |
| Lessons Learned | Case State, Learning Engine |
| Confidence Summary | Confidence Engine explanation and history |

## Interactions

- **Investigation Engine** — triggers report generation at `RESOLUTION`, `VERIFICATION`, and `CLOSED`.
- **State Machine** — `CLOSED` transition requires final report generation acknowledgment.
- **Evidence Engine** — supplies artifact metadata and summaries; raw content referenced by ID.
- **Reasoning Engine** — supplies RCA narrative and elimination sequence.
- **Confidence Engine** — supplies confidence explanation for RCA credibility section.
- **Topology Engine** — supplies structured topology for infrastructure section.
- **Question Engine** — supplies intake and investigation Q&A chronology.
- **Playbook Engine** — supplies verification checklist alignment.
- **Learning Engine** — receives closure report; contributes to organizational trend reports.
- **Knowledge Engine** — report templates and formatting standards.

### Report Integrity Rules

1. **No unsupported claims** — every root cause statement must cite evidence artifact IDs.
2. **Elimination transparency** — ruled-out hypotheses included with reasons.
3. **Confidence disclosure** — final confidence score and explanation in RCA.
4. **Immutable closure report** — final report version cannot be regenerated without audit entry.
5. **Audience-appropriate depth** — executive summary excludes CLI output; technical summary includes it.

## Future Extensions

- ITSM integration: push structured report sections to ServiceNow incident records.
- Compliance report packs: SOX, HIPAA telephony, E911 post-incident documentation.
- Multi-language report generation from same structured source.
- Report comparison: diff between initial hypothesis and final RCA.
- Automated stakeholder distribution with role-based section visibility.
- PDF and portal rendering from structured report model.
- Regulatory submission formats for carrier or government incident notification.

## Example Workflow

**Scenario:** VP-CUBE-0001 investigation closed.

1. **Resolution Report (Draft)** — Triggered on `RESOLUTION` entry. Report Engine assembles: incident summary, preliminary RCA, evidence collected to date. Marked draft pending verification.

2. **Timeline Construction** — Events ordered: case opened 09:00, intake complete 09:20, first CLI collected 09:45, local 404 identified 10:30, dial-peer config collected 11:00, root cause confirmed 11:45, fix applied 12:00.

3. **RCA Assembly** — Root cause: missing CUBE dial-peer for mobile prefixes. Evidence citations: E-003 (SIP debug, local 404), E-005 (dial-peer config gap). Elimination narrative: trunk down ruled by E-001; provider rejection ruled by local 404 origin. Confidence: 92 with explanation.

4. **Verification Report** — Triggered on `VERIFICATION` completion. Section added: local outbound pass, mobile outbound pass, international outbound pass, inbound regression pass.

5. **Executive Summary** — Generated for leadership: "Outbound PSTN calls failed for 6 hours affecting 200 users. Root cause: incomplete dial-peer configuration after change. Resolved and verified. Preventive action: dial-peer change checklist."

6. **Technical Summary** — Generated for engineering: full topology, CLI evidence summary, configuration diff, fix steps, debug interpretation.

7. **Closure Report** — Final immutable document on `CLOSED`. Learning Engine receives copy. Citation index archived for audit.

8. **Preventive Actions** — Documented: implement dial-peer validation script; add mobile test to change procedure; schedule review of all outbound peer coverage.
