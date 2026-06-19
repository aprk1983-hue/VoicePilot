# Learning Engine

## Purpose

The Learning Engine captures structured organizational knowledge from every closed investigation. It does not train an LLM. It builds an enterprise knowledge base of symptoms, environments, evidence patterns, root causes, resolutions, verifications, and lessons learned that future investigations can reference with deterministic retrieval.

This engine closes the loop between individual incident resolution and institutional voice operations maturity.

## Responsibilities

- Ingest structured closure packages from completed investigations.
- Store anonymized case intelligence: symptoms, topology patterns, evidence signatures, root causes, resolutions.
- Index learnings for retrieval by Knowledge Engine and Reasoning Engine.
- Capture verification outcomes and preventive actions for effectiveness tracking.
- Record lessons learned in structured form, not free-text-only archives.
- Support SME review workflow before learnings enter the global knowledge corpus.
- Track playbook effectiveness metrics from closure data.
- Identify recurring patterns: symptom + environment + root cause frequency.
- Prevent PII and customer-identifiable data from entering the learning corpus.
- Maintain learning lineage: source case, playbook version, confidence at closure.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Closure Package | Investigation Engine | Complete Case State at `LEARNING` phase |
| Evidence Summary | Evidence Engine | Key artifacts, signals, and quality scores |
| Hypothesis Graph | Reasoning Engine | Confirmed and eliminated hypotheses with rationale |
| Confidence Record | Confidence Engine | Final score, history, and explanation |
| Topology Template | Topology Engine | Reusable anonymized topology pattern |
| Playbook Record | Playbook Engine | Playbook ID, version, completion metrics |
| Verification Results | Investigation Engine | Test outcomes and regression status |
| Report Summary | Report Engine | RCA and preventive action sections |
| SME Review Decision | Human Curator | Approve, reject, or amend before publication |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Learning Record | Knowledge Engine | Structured case intelligence for corpus indexing |
| Pattern Index Updates | Reasoning Engine | Historical priors for hypothesis seeding |
| Playbook Effectiveness Metrics | Playbook Engine | Success rate, time-to-resolution, confidence curves |
| Recurrence Alerts | Investigation Engine | Similar past cases when new case matches pattern |
| Trend Reports | Report Engine (organizational) | Root cause frequency, MTTR trends |
| Topology Templates | Topology Engine | Reusable environment patterns |
| Lessons Learned Repository | Knowledge Engine | Searchable structured lessons |

## Internal State

- **Learning Record Store** — anonymized closed case intelligence records.
- **Pattern Index** — inverted indexes: symptom → root cause, topology → failure mode, evidence signature → hypothesis.
- **Playbook Metrics Aggregator** — per-playbook resolution statistics.
- **Review Queue** — learnings pending SME approval.
- **Anonymization Policy Registry** — rules for redacting identifiers before storage.
- **Lineage Graph** — links between learning records, playbooks, and knowledge artifacts.
- **Recurrence Matcher** — similarity scoring for new case vs. historical patterns.

### Learning Record Structure

```yaml
learning_id:
source_case_id:       # internal reference only; not exposed in retrieval
captured_at:
symptoms: []
environment:
  platforms: []
  topology_pattern:
  versions: []
evidence_signatures: []
  - type:
    signal:
    quality:
root_cause:
  category:
  description:
  evidence_refs: []    # anonymized artifact types, not raw content
resolution:
  actions: []
verification:
  results: []
  passed:
preventive_actions: []
lessons_learned: []
playbook:
  id:
  version:
confidence_at_closure:
time_to_resolution:
review_status:        # pending | approved | rejected
approved_by:
```

## Interactions

- **Investigation Engine** — submits closure package on `LEARNING` phase entry; receives recurrence alerts on new cases.
- **Knowledge Engine** — primary consumer of approved learning records; indexes into field intelligence corpus.
- **Reasoning Engine** — queries pattern index for hypothesis priors; does not auto-confirm from history alone.
- **Playbook Engine** — receives effectiveness metrics; informs playbook selection weighting.
- **Topology Engine** — receives and supplies reusable topology templates.
- **Confidence Engine** — receives baseline confidence curves; contributes closure confidence to metrics.
- **Report Engine** — organizational trend reports aggregate learning data.
- **Evidence Engine** — evidence signature patterns indexed for future parsing hints.

### Learning Rules

1. **No LLM training** — learning records are structured data for retrieval and analytics only.
2. **Anonymization mandatory** — no hostnames, IP addresses, phone numbers, or customer names in published records.
3. **SME review required** — learnings enter global corpus only after curator approval.
4. **History informs, never confirms** — Reasoning Engine may seed hypotheses from patterns but must still require evidence.
5. **Immutable source record** — learning records are append-only; amendments create new versions.

## Future Extensions

- Cross-tenant anonymized pattern sharing with opt-in federation.
- Automatic recurrence detection with "similar case" surfacing at intake.
- Root cause trend dashboards by platform, version, and provider.
- Preventive action effectiveness tracking over time.
- Integration with change management: correlate learnings with change types.
- Learning-driven playbook revision proposals for engineering review.
- Compliance retention policies and legal hold on learning records.

## Example Workflow

**Scenario:** VP-CUBE-0001 closed successfully.

1. **Closure Trigger** — Investigation Engine enters `LEARNING` state. Closure package assembled from Case State and engine outputs.

2. **Anonymization** — Learning Engine redacts: `dmz-cube-01` → `CUBE_DMZ_01`, `CarrierX` → `ITSP_PROVIDER_A`, engineer identities removed.

3. **Record Creation** — Learning record created:
   - Symptom: outbound PSTN failure, fast busy
   - Topology pattern: `cucm_cube_itsp`
   - Evidence signature: local `404` on CUBE, trunk registered
   - Root cause: dial-peer gap for mobile prefix
   - Resolution: add dial-peer for mobile pattern
   - Verification: local, mobile, international pass
   - Lesson: "After dial-peer edits, validate all destination classes including mobile"

4. **Review Queue** — Record enters `pending` review. Voice SME approves with minor amendment to lesson text.

5. **Knowledge Indexing** — Approved record indexed in Knowledge Engine field intelligence corpus, linked to `VP-CUBE-0001`.

6. **Playbook Metrics** — Playbook Engine updated: resolution time 4.2 hours, closure confidence 92, verification first-pass success.

7. **Future Recurrence** — New case opens with same symptom and topology pattern. Learning Engine alerts Investigation Engine: "Similar approved learning exists (learning_id L-0042). Suggested evidence: check mobile dial-peer coverage." Reasoning Engine seeds dial-peer hypothesis with elevated priority — evidence still required.
