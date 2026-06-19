# Evidence Engine

## Purpose

The Evidence Engine is the forensic discipline layer of VoicePilot. It defines what evidence is required, tracks what has been collected, assesses evidence quality, and maintains the evidential timeline that anchors every diagnostic conclusion. Without this engine, VoicePilot would be an opinion generator. With it, VoicePilot operates like a TAC engineer who documents every show command, log excerpt, and test result before drawing conclusions.

**Core principle:** No evidence artifact enters Case State without provenance, quality assessment, and investigative relevance tagging.

## Responsibilities

- Define required and optional evidence sets based on playbook, topology, and active hypotheses.
- Track collected evidence, missing evidence, and explicitly waived evidence with rationale.
- Assess evidence quality: completeness, freshness, source reliability, and parseability.
- Record evidence source: human submission, automated collection, derived artifact, or third-party system.
- Assign per-artifact confidence contribution based on quality and relevance.
- Maintain evidence timeline aligned with case timeline and recent changes.
- Parse raw submissions (CLI output, logs, configs) into structured signals for the Reasoning Engine.
- Detect duplicate, superseded, and stale evidence artifacts.
- Block root cause confirmation when mandatory evidence remains missing or below quality threshold.
- Link evidence bidirectionally to hypotheses and investigative actions that produced it.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Evidence Requirements | Playbook Engine, Knowledge Engine | Mandatory and optional artifacts per scenario and phase |
| Raw Submissions | Engineer, Automation Connectors | CLI output, debug logs, configs, packet captures, test results |
| Hypothesis Context | Reasoning Engine | Evidence needed to confirm or eliminate specific hypotheses |
| Topology Context | Topology Engine | Which components evidence must be collected from |
| Case Timeline | Investigation Engine | Incident onset, change windows, collection timestamps |
| Collection Directives | Investigation Engine | Specific commands or artifacts requested |
| Parsing Rules | Knowledge Engine | Output patterns, field extractions, error signature definitions |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Evidence Artifacts | Case State | Structured evidence records with metadata |
| Missing Evidence Report | Investigation Engine, Question Engine | Prioritized gaps blocking progress or confirmation |
| Parsed Signals | Reasoning Engine | Extracted facts: SIP codes, dial-peer matches, error strings, state values |
| Quality Assessments | Confidence Engine | Per-artifact and aggregate evidence quality scores |
| Evidence Timeline | Report Engine | Chronological collection and relevance map |
| Collection Plan | Investigation Engine | Next artifacts to collect with commands and target devices |
| Supersession Notices | Investigation Engine | When newer evidence replaces older artifacts |

## Internal State

- **Evidence Registry** — all artifacts per case with immutable submission records.
- **Requirement Tracker** — mandatory, optional, and satisfied requirements with waiver status.
- **Quality Score Cache** — per-artifact scores and aggregate case evidence health.
- **Parse Result Store** — structured extractions linked to raw artifact hashes.
- **Source Reliability Table** — human-verified, automated, inferred; per-source weighting.
- **Timeline Index** — evidence ordered by collection time, relevance window, and hypothesis linkage.
- **Deduplication Index** — content hashes to prevent duplicate artifact inflation.

### Evidence Artifact Structure

```yaml
evidence_id:
case_id:
type:           # cli_output | config_excerpt | debug_log | test_result | screenshot | packet_capture
title:
source:
  origin:       # human | connector | derived
  collector:    # engineer identity or system identity
  device:       # hostname, role, management address
  command:      # if CLI-derived
collected_at:
raw_content_ref:
parsed_signals: []
quality:
  completeness:
  freshness:
  reliability:
  parseability:
  overall:
relevance:
  hypotheses_supported: []
  hypotheses_contradicted: []
  investigation_phase:
status:         # submitted | parsed | validated | superseded | rejected
supersedes:
superseded_by:
```

## Interactions

- **Investigation Engine** — issues collection directives; receives gap reports and collection plans.
- **Reasoning Engine** — supplies parsed signals; receives targeted collection recommendations.
- **Knowledge Engine** — provides command libraries, parsing rules, and interpretation standards.
- **Playbook Engine** — defines scenario-specific required evidence sets.
- **Confidence Engine** — supplies quality scores and coverage metrics for confidence calculation.
- **Question Engine** — missing evidence may trigger clarifying questions before collection.
- **Topology Engine** — identifies which network elements evidence must be sourced from.
- **Report Engine** — provides evidence appendix and timeline for incident documentation.
- **Learning Engine** — contributes anonymized evidence patterns from closed cases.

## Future Extensions

- Automated read-only collection connectors for CUCM, CUBE, Expressway with credential vault integration.
- Differential evidence analysis: compare current config to last known good baseline.
- Log correlation across CUCM, CUBE, and firewall timestamps with clock skew adjustment.
- Evidence chain of custody for compliance and legal discovery scenarios.
- ML-assisted parsing with human validation gate (parser suggests, engineer confirms).
- Real-time streaming evidence ingestion during active debug sessions.
- Evidence redaction pipeline for sensitive data before storage or report export.

## Example Workflow

**Scenario:** VP-CUBE-0001 outbound failure investigation.

1. **Requirement Initialization** — Playbook Engine defines mandatory evidence: `show dial-peer voice summary`, `show sip-ua status`, `show run | sec dial-peer`, SIP debug for failing call. Evidence Engine populates `missing_evidence` in Case State.

2. **First Submission** — Engineer uploads `show sip-ua status` output. Evidence Engine records artifact, assigns source reliability "human-verified", parses registration state: all SIP peers UP. Quality: completeness high, freshness current. Signals forwarded to Reasoning Engine.

3. **Debug Log Submission** — Engineer provides `debug ccsip messages` excerpt. Parser extracts: INVITE sent, `404 Not Found` received, response origin tagged as local. Quality: completeness medium (single call sample). Linked to dial-peer mismatch hypothesis.

4. **Gap Detection** — `show run | sec dial-peer` still missing. Evidence Engine flags as blocking for root cause confirmation. Investigation Engine receives prioritized collection plan.

5. **Config Submission** — Engineer provides dial-peer configuration. Parser extracts peer patterns, destinations, codec lists. Cross-references topology: CUBE outbound path. Quality: high. Mandatory set now satisfied except verification test results.

6. **Stale Evidence Warning** — Engineer submits new `show sip-ua status` after configuration change. Evidence Engine supersedes prior artifact, recalculates signals, notifies Reasoning Engine of evidence refresh.

7. **Closure Evidence** — Post-resolution test results submitted: mobile outbound successful. Evidence Engine tags as verification evidence, links to resolution record, updates timeline for Report Engine.
