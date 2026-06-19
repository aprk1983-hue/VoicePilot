# Playbook Engine

## Purpose

The Playbook Engine operationalizes institutional TAC knowledge into executable investigation procedures. It loads vendor-specific playbooks, selects the best match for a given incident, guides phase-aligned investigation steps, and supports controlled playbook switching when investigation scope changes. Playbooks are not scripts; they are structured investigation frameworks that engines interpret.

## Responsibilities

- Maintain a catalog of investigation playbooks across vendors and scenarios.
- Select the best playbook based on symptom, platform, topology, and business context.
- Bind an active playbook to a case and track alignment with lifecycle state.
- Provide phase-specific guidance: intake questions, evidence requirements, hypothesis seeds, verification steps.
- Support playbook switching mid-investigation with state preservation and transition rationale.
- Enforce playbook versioning: investigations record which playbook version was applied.
- Coordinate multi-vendor playbooks when topology spans Cisco, Microsoft, and third-party SBCs.
- Surface playbook escalation criteria and recommended SME involvement triggers.
- Validate that investigation progress satisfies playbook completion criteria before closure.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Symptom & Platform | Investigation Engine | Initial case characteristics |
| Topology Model | Topology Engine | Components and paths in affected environment |
| Knowledge Catalog | Knowledge Engine | Playbook definitions, metadata, applicability rules |
| Case State | Investigation Engine | Current phase, collected evidence, active hypotheses |
| Switch Request | Investigation Engine | Scope change, new symptoms, vendor discovery |
| Engineer Override | Human Operator | Explicit playbook selection with documented reason |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Selected Playbook | Investigation Engine, Case State | Playbook ID, version, binding timestamp |
| Phase Guidance | Question, Evidence, Reasoning Engines | Step requirements per lifecycle phase |
| Required Evidence Set | Evidence Engine | Mandatory and optional artifacts |
| Intake Question Bank | Question Engine | Playbook-defined and ranked questions |
| Hypothesis Seeds | Reasoning Engine | Initial candidate hypotheses for scenario |
| Verification Checklist | Investigation Engine, Report Engine | Post-resolution test requirements |
| Switch Recommendation | Investigation Engine | When current playbook is poor fit |
| Completion Status | State Machine | Playbook criteria satisfied for closure |

## Internal State

- **Playbook Catalog** — indexed by vendor, symptom, component, severity, and topology pattern.
- **Active Binding Table** — `case_id` → active playbook, version, bind time, switch history.
- **Phase Alignment Map** — playbook phases mapped to State Machine states.
- **Applicability Scoring Cache** — last computed match scores per case.
- **Switch Policy Registry** — rules for when automatic switch recommendation is triggered.
- **Completion Tracker** — per-case checklist of playbook requirements satisfied.

### Playbook Structure

```yaml
playbook_id:        # e.g., VP-CUBE-0001
version:
vendor:
category:
title:
symptoms: []
business_impact:
applicability:
  platforms: []
  topology_patterns: []
  required_components: []
phases:
  intake:
    questions: []
  discovery: {}
  collection:
    required_commands: []
    required_logs: []
  analysis:
    hypothesis_seeds: []
    evidence_rules: []
  verification:
    steps: []
  learning:
    capture_fields: []
escalation_criteria: []
related_playbooks: []
```

## Interactions

- **Investigation Engine** — requests playbook selection, binding, and completion validation.
- **Knowledge Engine** — playbook content storage and retrieval; playbook metadata is part of knowledge corpus.
- **Question Engine** — receives intake and phase-specific question banks.
- **Evidence Engine** — receives required and optional evidence definitions.
- **Reasoning Engine** — receives hypothesis seeds and evidence interpretation rules.
- **Topology Engine** — provides topology pattern matching for playbook applicability.
- **State Machine** — playbook phase alignment informs valid state transitions.
- **Confidence Engine** — playbook may define minimum evidence standards for scenario.
- **Learning Engine** — closed case playbook performance feeds selection model improvement.

## Future Extensions

- Playbook composition: chain sub-playbooks for multi-vendor paths (Teams + CUBE + ITSP).
- Playbook A/B effectiveness tracking from Learning Engine closure data.
- Customer-specific playbook overlays without modifying global catalog.
- Auto-generated playbook draft suggestions from recurring Learning Engine patterns.
- Playbook dependency graph for related and superseding procedures.
- Regulatory playbook packs (E911, lawful intercept) with mandatory step enforcement.
- Playbook simulation mode for training without live case binding.

## Example Workflow

**Scenario:** Outbound PSTN failure on Cisco CUBE.

1. **Selection** — Investigation Engine opens case with symptom "outbound PSTN failure", platform "Cisco CUBE". Playbook Engine scores catalog entries. `VP-CUBE-0001` scores highest (symptom match, topology contains CUBE, outbound path).

2. **Binding** — Playbook `VP-CUBE-0001` v1.0 bound to case. Phase alignment: intake → `INTAKE`, collection → `COLLECTION`. Recorded in Case State.

3. **Intake Guidance** — Question Engine receives playbook intake questions: "Did this ever work?", "Recent changes?", "All outbound or selective?" Evidence Engine receives future requirements preview.

4. **Mid-Investigation Discovery** — Engineer reveals Expressway also in path for some sites. Topology Engine updates model. Playbook Engine evaluates switch: `VP-CUBE-0001` still primary for CUBE path; recommends supplemental Expressway knowledge pack, no full switch.

5. **Scope Change** — New symptom: Teams Direct Routing also affected. Playbook Engine recommends switch to composite workflow: `VP-CUBE-0001` + `VP-TEAMS-DR-0003`. Investigation Engine approves switch. Switch history recorded.

6. **Verification** — Playbook verification checklist: local outbound, mobile outbound, international outbound, inbound regression test. Investigation Engine validates each step before Playbook Engine marks completion.

7. **Closure** — Playbook Engine reports all completion criteria satisfied. State Machine permitted to advance to `LEARNING` and `CLOSED`.
