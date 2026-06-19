# VoicePilot Canonical Data Model

## 1. Purpose

The VoicePilot Canonical Data Model defines the structured objects through which all Brain engines communicate. VoicePilot is not a chatbot. It is an AI Voice Operations Engineer that investigates incidents with TAC discipline. Engines do not exchange ambiguous free text as system of record — they read and write typed, auditable objects with explicit relationships.

The Case object is the root aggregate. Every investigation artifact — evidence, hypotheses, decisions, topology, timeline events — links back to a Case. This model is vendor-neutral at the schema level while supporting Cisco, Microsoft Teams, SIP, RTP, SBCs, and future platforms through extensible metadata.

**Specification status:** Architecture draft — Sprint 0, Day 3.

---

## 2. Design Principles

| Principle | Description |
|-----------|-------------|
| Case as Root | Every object belongs to exactly one Case or references a Case-scoped entity |
| Structured Over Conversational | Canonical objects are authoritative; chat is a presentation layer only |
| Evidence Provenance | Evidence links to source artifacts (CLI, logs, configs) with collector and timestamp |
| Hypothesis Linkage | Hypotheses declare supporting and contradicting evidence explicitly |
| Decision Transparency | Decisions document alternatives considered and rejection reasons |
| Explainable Confidence | Confidence scores include factor breakdown and human-readable explanation |
| No Root Cause Without Evidence | Root cause confirmation requires evidence references and confidence gate pass |
| Vendor Neutrality | Platform specifics live in typed metadata, not schema forks |
| Enterprise Auditability | Immutable identifiers, append-only history, actor attribution on mutations |
| Engineer in Control | Recommendations require acknowledgment; disruptive actions include rollback |
| Graph Compatibility | Objects map to Investigation Graph nodes and edges without duplication of truth |
| Extensibility | Custom fields via namespaced `extensions` blocks without breaking core schema |

---

## 3. Core Object List

| Object | ID Prefix | Owning Engine(s) | Description |
|--------|-----------|------------------|-------------|
| Case | `CASE-` | Investigation Engine | Root investigation aggregate |
| Evidence | `EVD-` | Evidence Engine | Collected proof with provenance |
| Hypothesis | `HYP-` | Reasoning Engine | Candidate or confirmed root cause |
| Decision | `DEC-` | Decision Engine | Recorded technical decision |
| Question | `QST-` | Question Engine | TAC-style investigative question |
| InvestigationStep | `STEP-` | Investigation Planner | Planned or executed investigative action |
| TimelineEvent | `TLE-` | Timeline Engine | Chronological investigation event |
| Topology | `TOPO-` | Topology Engine | Voice path model for the case |
| Device | `DEV-` | Topology Engine | Infrastructure component instance |
| Configuration | `CFG-` | Evidence Engine | Configuration excerpt artifact |
| LogArtifact | `LOG-` | Evidence Engine | Log or debug output artifact |
| ParserFinding | `FIND-` | Evidence Engine | Structured signal from parsed artifact |
| Playbook | `PB-` | Playbook Engine | Investigation procedure definition |
| KnowledgeItem | `KNW-` | Knowledge Engine | Curated domain knowledge reference |
| ConfidenceScore | `CONF-` | Confidence Engine | Point-in-time confidence assessment |
| Recommendation | `REC-` | Cost Optimizer, Investigation Planner | Proposed next action |
| Verification | `VER-` | Investigation Engine | Post-resolution test record |
| Report | `RPT-` | Report Engine | Generated investigation deliverable |
| LearningRecord | `LRN-` | Learning Engine | Anonymized post-closure knowledge |
| InvestigationGraph | `GRPH-` | Investigation Graph | Node/edge reasoning model |

---

## 4. Object Relationships

```
                              ┌─────────────┐
                              │    Case     │
                              └──────┬──────┘
         ┌──────────┬───────────┼───────────┬──────────┬──────────┐
         ▼          ▼           ▼           ▼          ▼          ▼
    Evidence   Hypothesis   Decision    Question  Topology  TimelineEvent
         │          │           │           │          │
         │          │           │           │          ▼
         │          │           │           │       Device
         │          │           │           │          │
         ▼          │           │           │          ▼
   LogArtifact      │           │           │   Configuration
   Configuration    │           │           │
         │          │           │           │
         ▼          ▼           ▼           ▼
   ParserFinding ◄──┴───────────┴───────────┘
         │
         ▼
 InvestigationGraph (nodes/edges reference all above)
         │
    ┌────┴────┬────────────┬─────────────┬──────────────┐
    ▼         ▼            ▼             ▼              ▼
ConfidenceScore Recommendation Verification  Report  LearningRecord
    │              │
    └──────┬───────┘
           ▼
      Playbook ──► KnowledgeItem (references)
```

**Cardinality rules:**

- Case 1 → N for all child objects
- Evidence 1 → N ParserFinding
- LogArtifact | Configuration 1 → 1 Evidence (artifact is source)
- Hypothesis N ↔ N Evidence (supporting / contradicting)
- Decision N → N Evidence; Decision N → 0..1 Hypothesis
- Recommendation 1 → 0..1 InvestigationStep
- Verification N → 1 Case; links to Recommendation or Resolution
- Report 1 → 1 Case (versioned)
- LearningRecord 1 → 1 Case (anonymized derivative)
- InvestigationGraph 1 → 1 Case

---

## 5. Case Object

### Purpose

The Case is the root aggregate and single source of truth for an investigation. All engines mutate Case-scoped objects through the Investigation Engine.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | string | yes | Unique identifier (`CASE-{uuid}`) |
| `title` | string | yes | Human-readable incident title |
| `status` | enum | yes | Lifecycle state (State Machine) |
| `severity` | enum | yes | critical, high, medium, low |
| `business_impact` | string | yes | Impact description |
| `symptom` | SymptomRef | yes | Primary symptom object or inline |
| `affected_scope` | object | yes | Sites, users, number ranges |
| `platform` | PlatformRef | yes | Vendor-neutral platform descriptor |
| `strategy` | StrategyRef | no | Active investigation strategy |
| `playbook_id` | string | no | Bound playbook reference |
| `assigned_engineer` | string | no | Owner identity |
| `opened_at` | datetime | yes | Case creation timestamp |
| `closed_at` | datetime | no | Closure timestamp |
| `root_cause_id` | string | no | Confirmed hypothesis or root cause ref |
| `resolution_summary` | string | no | Brief resolution description |
| `confidence_score_id` | string | no | Latest confidence snapshot ref |
| `schema_version` | string | yes | Data model version |

### Relationships

- Parent of: Evidence, Hypothesis, Decision, Question, InvestigationStep, TimelineEvent, Topology, Verification, Report, InvestigationGraph, ConfidenceScore
- References: Playbook, Platform devices via Topology

### Example YAML

```yaml
case_id: CASE-7f3a2b1c
title: Outbound PSTN calls fail — HQ site
status: INVESTIGATION
severity: high
business_impact: All outbound PSTN calls failing for ~200 users at HQ
symptom:
  summary: Outbound PSTN failure with fast busy
  onset: 2026-06-18T14:00:00Z
  failure_mode: fast_busy
affected_scope:
  sites: [HQ]
  call_direction: outbound
  destination_classes: [mobile, landline]
platform:
  vendor: cisco
  products: [cucm, cube]
  version_hints:
    cube: "16.12.4"
strategy:
  strategy_id: routing-first
  bound_at: 2026-06-19T09:05:00Z
playbook_id: VP-CUBE-0001
assigned_engineer: engineer@example.com
opened_at: 2026-06-19T09:00:00Z
schema_version: "1.0"
```

---

## 6. Evidence Object

### Purpose

Evidence represents a collected investigative artifact with full provenance. Evidence is the foundation of all conclusions.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_id` | string | yes | `EVD-{uuid}` |
| `case_id` | string | yes | Parent case |
| `type` | enum | yes | cli_output, config_excerpt, debug_log, test_result, packet_capture, screenshot |
| `title` | string | yes | Short description |
| `source_artifact_id` | string | yes | LogArtifact, Configuration, or external ref |
| `source` | object | yes | origin, collector, device_id, command |
| `collected_at` | datetime | yes | Collection timestamp |
| `quality` | object | yes | completeness, freshness, reliability, parseability, overall |
| `status` | enum | yes | submitted, parsed, validated, superseded, rejected |
| `parser_finding_ids` | string[] | no | Extracted signals |
| `supports_hypothesis_ids` | string[] | no | Linked hypotheses |
| `contradicts_hypothesis_ids` | string[] | no | Linked hypotheses |
| `supersedes` | string | no | Prior evidence_id |
| `superseded_by` | string | no | Replacing evidence_id |

### Relationships

- Belongs to: Case
- Source: LogArtifact | Configuration | Device
- Produces: ParserFinding[]
- Linked by: Hypothesis (support/contradict), Decision, InvestigationGraph

### Example YAML

```yaml
evidence_id: EVD-002
case_id: CASE-7f3a2b1c
type: debug_log
title: CCSIP messages for failing mobile outbound call
source_artifact_id: LOG-002
source:
  origin: human
  collector: engineer@example.com
  device_id: DEV-cube-01
  command: debug ccsip messages
collected_at: 2026-06-19T10:00:00Z
quality:
  completeness: 0.75
  freshness: 1.0
  reliability: 0.9
  parseability: 0.85
  overall: 0.87
status: parsed
parser_finding_ids: [FIND-001, FIND-002]
supports_hypothesis_ids: [HYP-dp-001]
contradicts_hypothesis_ids: [HYP-provider-001]
```

---

## 7. Hypothesis Object

### Purpose

A Hypothesis is a candidate or confirmed explanation for the incident. Hypotheses are never elevated without evidence linkage.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hypothesis_id` | string | yes | `HYP-{uuid}` |
| `case_id` | string | yes | Parent case |
| `title` | string | yes | Concise hypothesis statement |
| `description` | string | no | Detailed explanation |
| `status` | enum | yes | candidate, active, confirmed, eliminated |
| `category` | string | no | routing, provider, network, media, security, change |
| `affected_device_ids` | string[] | no | Topology devices |
| `supporting_evidence_ids` | string[] | yes* | *Required for active/confirmed |
| `contradicting_evidence_ids` | string[] | no | Evidence against |
| `knowledge_item_ids` | string[] | no | Supporting knowledge refs |
| `rank` | integer | no | Current ranking position |
| `confidence_contribution` | number | no | Input to Confidence Engine |
| `elimination_decision_id` | string | no | Decision that eliminated |
| `created_at` | datetime | yes | Creation timestamp |

### Relationships

- Belongs to: Case
- N ↔ N: Evidence
- 0..1: Decision (elimination or confirmation)
- Node in: InvestigationGraph

### Example YAML

```yaml
hypothesis_id: HYP-dp-001
case_id: CASE-7f3a2b1c
title: CUBE dial-peer mismatch for mobile destinations
description: Outbound mobile calls match no valid dial-peer or match wrong peer
status: confirmed
category: routing
affected_device_ids: [DEV-cube-01]
supporting_evidence_ids: [EVD-002, EVD-005]
contradicting_evidence_ids: []
knowledge_item_ids: [KNW-cube-local-404]
rank: 1
confidence_contribution: 0.92
created_at: 2026-06-19T10:10:00Z
```

---

## 8. Decision Object

### Purpose

A Decision records a significant technical conclusion or choice with full audit metadata.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision_id` | string | yes | `DEC-{uuid}` |
| `case_id` | string | yes | Parent case |
| `sequence` | integer | yes | Monotonic order per case |
| `type` | enum | yes | elimination, confirmation, strategy, gate, waiver, escalation |
| `decision` | string | yes | What was decided |
| `reason` | string | yes | Why |
| `evidence_ids` | string[] | yes* | *Required for elimination/confirmation |
| `confidence` | number | yes | Score at decision time |
| `timestamp` | datetime | yes | Decision time |
| `actor` | string | yes | Engine or engineer identity |
| `alternatives_considered` | object[] | yes | alternative, rejection_reason |
| `hypothesis_id` | string | no | Affected hypothesis |
| `state_at_decision` | enum | yes | Lifecycle state |
| `engineer_acknowledged` | boolean | yes | Engineer approval flag |
| `supersedes` | string | no | Prior decision_id |
| `superseded_by` | string | no | Superseding decision_id |

### Relationships

- Belongs to: Case
- References: Evidence[], Hypothesis
- Produces: TimelineEvent
- Node in: InvestigationGraph

### Example YAML

```yaml
decision_id: DEC-003
case_id: CASE-7f3a2b1c
sequence: 3
type: elimination
decision: Eliminate provider-side rejection as root cause
reason: SIP 404 generated locally on CUBE before ITSP response
evidence_ids: [EVD-002]
confidence: 91
timestamp: 2026-06-19T10:18:00Z
actor: reasoning-engine
alternatives_considered:
  - alternative: ITSP routing rejection (503/404 from carrier)
    rejection_reason: Response origin attribute indicates local CUBE generation
hypothesis_id: HYP-provider-001
state_at_decision: INVESTIGATION
engineer_acknowledged: true
```

---

## 9. Question Object

### Purpose

A Question is a structured TAC-style inquiry with tracked status and answer mapping to Case fields.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_id` | string | yes | `QST-{uuid}` |
| `case_id` | string | yes | Parent case |
| `text` | string | yes | Question presented to engineer |
| `category` | enum | yes | intake, topology, scope, change, discrimination, verification |
| `phase` | enum | yes | Lifecycle phase when asked |
| `source` | enum | yes | playbook, topology_gap, reasoning, knowledge |
| `target_fields` | string[] | no | Case State fields answer populates |
| `information_gain_score` | number | no | Question Engine ranking |
| `status` | enum | yes | pending, asked, answered, deferred, waived |
| `asked_at` | datetime | no | When presented |
| `answered_at` | datetime | no | When answered |
| `answer_structured` | object | no | Typed answer payload |
| `hypothesis_ids` | string[] | no | Hypotheses this discriminates |

### Relationships

- Belongs to: Case
- May reference: Hypothesis[], Playbook, KnowledgeItem
- Node in: InvestigationGraph

### Example YAML

```yaml
question_id: QST-001
case_id: CASE-7f3a2b1c
text: Are failing calls limited to mobile numbers, or also landline?
category: discrimination
phase: INVESTIGATION
source: reasoning
target_fields: [affected_scope.destination_classes]
information_gain_score: 0.88
status: answered
asked_at: 2026-06-19T09:50:00Z
answered_at: 2026-06-19T09:52:00Z
answer_structured:
  mobile_only: true
  landline_affected: false
hypothesis_ids: [HYP-dp-001, HYP-provider-001]
```

---

## 10. Investigation Step Object

### Purpose

An Investigation Step is a planned or executed action in the investigation plan — a question, collection, test, or configuration review.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_id` | string | yes | `STEP-{uuid}` |
| `case_id` | string | yes | Parent case |
| `sequence` | integer | yes | Plan order |
| `action_type` | enum | yes | ask_question, collect_evidence, run_test, review_config, apply_fix |
| `description` | string | yes | What to do |
| `target_device_id` | string | no | Device if applicable |
| `command` | string | no | CLI command if applicable |
| `cost_level` | enum | yes | low, medium, high, critical |
| `status` | enum | yes | planned, recommended, approved, in_progress, completed, skipped |
| `recommendation_id` | string | no | Source recommendation |
| `evidence_id` | string | no | Produced evidence |
| `question_id` | string | no | Related question |
| `engineer_approved` | boolean | no | Required for high/critical |
| `completed_at` | datetime | no | Completion time |

### Relationships

- Belongs to: Case
- Created by: Investigation Planner, Cost Optimizer
- Produces: Evidence, Question
- Linked from: Recommendation

### Example YAML

```yaml
step_id: STEP-004
case_id: CASE-7f3a2b1c
sequence: 4
action_type: collect_evidence
description: Collect dial-peer configuration from CUBE
target_device_id: DEV-cube-01
command: show run | sec dial-peer
cost_level: low
status: completed
recommendation_id: REC-003
evidence_id: EVD-005
engineer_approved: true
completed_at: 2026-06-19T11:00:00Z
```

---

## 11. Timeline Event Object

### Purpose

A Timeline Event is an immutable chronological record of something that happened during the investigation.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | yes | `TLE-{uuid}` |
| `case_id` | string | yes | Parent case |
| `sequence` | integer | yes | Order within case |
| `timestamp` | datetime | yes | Event time |
| `event_type` | enum | yes | case_opened, evidence_collected, hypothesis_eliminated, decision_recorded, etc. |
| `source_engine` | string | yes | Producing engine |
| `summary` | string | yes | Human-readable summary |
| `related_entity_ids` | object | no | Typed refs (evidence_id, decision_id, etc.) |
| `case_state_snapshot_ref` | string | no | Snapshot at milestone |
| `engineer_visible` | boolean | yes | Show in engineer timeline |

### Relationships

- Belongs to: Case
- References: any Case-scoped entity

### Example YAML

```yaml
event_id: TLE-012
case_id: CASE-7f3a2b1c
sequence: 12
timestamp: 2026-06-19T10:18:00Z
event_type: decision_recorded
source_engine: decision-engine
summary: Eliminated provider rejection hypothesis
related_entity_ids:
  decision_id: DEC-003
  hypothesis_id: HYP-provider-001
engineer_visible: true
```

---

## 12. Topology Object

### Purpose

Topology models the voice infrastructure and call path for the investigation.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topology_id` | string | yes | `TOPO-{uuid}` |
| `case_id` | string | yes | Parent case |
| `pattern` | string | yes | Reference pattern (e.g., cucm_cube_itsp) |
| `device_ids` | string[] | yes | Component devices |
| `relationships` | object[] | yes | from, to, type, attributes |
| `call_paths` | object[] | no | Signaling and media paths |
| `completeness` | object | yes | score, missing_elements |
| `validation` | object | yes | consistent, issues |
| `updated_at` | datetime | yes | Last update |

### Relationships

- Belongs to: Case
- Contains: Device[]
- Referenced by: Evidence, Hypothesis, InvestigationGraph

### Example YAML

```yaml
topology_id: TOPO-001
case_id: CASE-7f3a2b1c
pattern: cucm_cube_itsp
device_ids: [DEV-cucm-01, DEV-cube-01, DEV-itsp-01]
relationships:
  - from: DEV-cucm-01
    to: DEV-cube-01
    type: sip_trunk
    attributes:
      trunk_name: CUBE-SIP-TRUNK
  - from: DEV-cube-01
    to: DEV-itsp-01
    type: sip_trunk
    attributes:
      provider: CarrierX
call_paths:
  - name: outbound_pstn
    signaling: [DEV-cucm-01, DEV-cube-01, DEV-itsp-01]
    media: [DEV-cucm-01, DEV-cube-01, DEV-itsp-01]
completeness:
  score: 0.85
  missing_elements: []
validation:
  consistent: true
  issues: []
updated_at: 2026-06-19T09:25:00Z
```

---

## 13. Device Object

### Purpose

A Device represents an infrastructure component in the voice topology. Vendor-neutral core with extensible platform metadata.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | string | yes | `DEV-{uuid}` |
| `case_id` | string | yes | Parent case (or shared inventory ref) |
| `type` | enum | yes | cucm, cube, expressway, teams_tenant, sbc, firewall, gateway, provider, endpoint |
| `role` | string | yes | e.g., call_manager, session_border, itsp |
| `hostname` | string | no | Device hostname |
| `management_address` | string | no | Management IP/FQDN |
| `vendor` | string | yes | cisco, microsoft, audiocodes, ribbon, generic |
| `product` | string | no | Product name |
| `version` | string | no | Software version |
| `zone` | string | no | Network zone (dmz, internal, cloud) |
| `extensions` | object | no | Vendor-specific attributes |

### Relationships

- Belongs to: Topology, Case
- Source of: Evidence, Configuration, LogArtifact
- Node in: InvestigationGraph

### Example YAML

```yaml
device_id: DEV-cube-01
case_id: CASE-7f3a2b1c
type: cube
role: session_border
hostname: dmz-cube-01.example.com
vendor: cisco
product: CUBE
version: "16.12.4"
zone: dmz
extensions:
  ios_mode: ISR
  sip_profiles: [voice-service-voip]
```

---

## 14. Configuration Object

### Purpose

A Configuration object is a captured configuration excerpt stored as a source artifact for Evidence.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `configuration_id` | string | yes | `CFG-{uuid}` |
| `case_id` | string | yes | Parent case |
| `device_id` | string | yes | Source device |
| `section` | string | yes | Config section (dial-peer, voice service, trunk) |
| `capture_method` | enum | yes | cli, export, api, manual |
| `command` | string | no | CLI used |
| `content_hash` | string | yes | Integrity hash |
| `content_ref` | string | yes | Storage reference for raw content |
| `captured_at` | datetime | yes | Capture time |
| `captured_by` | string | yes | Collector identity |

### Relationships

- Belongs to: Case, Device
- Source for: Evidence

### Example YAML

```yaml
configuration_id: CFG-005
case_id: CASE-7f3a2b1c
device_id: DEV-cube-01
section: dial-peer
capture_method: cli
command: show run | sec dial-peer
content_hash: sha256:a1b2c3...
content_ref: artifact-store://CASE-7f3a2b1c/CFG-005
captured_at: 2026-06-19T11:00:00Z
captured_by: engineer@example.com
```

---

## 15. Log Artifact Object

### Purpose

A Log Artifact stores raw log, debug, or syslog output as a source artifact for Evidence.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `log_artifact_id` | string | yes | `LOG-{uuid}` |
| `case_id` | string | yes | Parent case |
| `device_id` | string | no | Source device |
| `log_type` | enum | yes | debug, syslog, cdr, sip_trace, rtp_trace |
| `capture_method` | enum | yes | cli, file_upload, connector |
| `command` | string | no | Debug command if applicable |
| `content_hash` | string | yes | Integrity hash |
| `content_ref` | string | yes | Storage reference |
| `line_count` | integer | no | Size indicator |
| `time_range` | object | no | start, end of log coverage |
| `captured_at` | datetime | yes | Capture time |
| `captured_by` | string | yes | Collector identity |

### Relationships

- Belongs to: Case, Device
- Source for: Evidence
- Produces: ParserFinding (via parsing)

### Example YAML

```yaml
log_artifact_id: LOG-002
case_id: CASE-7f3a2b1c
device_id: DEV-cube-01
log_type: sip_trace
capture_method: cli
command: debug ccsip messages
content_hash: sha256:d4e5f6...
content_ref: artifact-store://CASE-7f3a2b1c/LOG-002
line_count: 342
time_range:
  start: 2026-06-19T09:58:00Z
  end: 2026-06-19T10:01:00Z
captured_at: 2026-06-19T10:00:00Z
captured_by: engineer@example.com
```

---

## 16. Parser Finding Object

### Purpose

A Parser Finding is a structured signal extracted from a log or configuration artifact by the Evidence Engine.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `finding_id` | string | yes | `FIND-{uuid}` |
| `case_id` | string | yes | Parent case |
| `evidence_id` | string | yes | Parent evidence |
| `source_artifact_id` | string | yes | LOG or CFG ref |
| `signal_type` | enum | yes | sip_response_code, dial_peer_match, registration_state, error_string, config_pattern |
| `signal_value` | string | yes | Extracted value |
| `context` | object | no | Surrounding context (call-id, peer, timestamp) |
| `interpretation` | string | no | Knowledge-guided meaning |
| `confidence` | number | no | Parser confidence |
| `knowledge_item_id` | string | no | Interpretation rule ref |

### Relationships

- Belongs to: Evidence
- Informs: Hypothesis, Decision, InvestigationGraph

### Example YAML

```yaml
finding_id: FIND-001
case_id: CASE-7f3a2b1c
evidence_id: EVD-002
source_artifact_id: LOG-002
signal_type: sip_response_code
signal_value: "404"
context:
  response_origin: local
  method: INVITE
  called_number: "+15551234567"
interpretation: 404 generated locally on CUBE — routing/dial-peer issue likely
confidence: 0.95
knowledge_item_id: KNW-cube-local-404
```

---

## 17. Playbook Object

### Purpose

A Playbook defines a structured investigation procedure for a vendor scenario. Referenced by cases; content owned by Knowledge Engine.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `playbook_id` | string | yes | e.g., VP-CUBE-0001 |
| `version` | string | yes | Semantic version |
| `vendor` | string | yes | Primary vendor |
| `category` | string | yes | Scenario category |
| `title` | string | yes | Playbook title |
| `symptoms` | string[] | yes | Matching symptoms |
| `applicability` | object | yes | platforms, topology_patterns, components |
| `phases` | object | yes | intake, collection, analysis, verification |
| `required_evidence` | string[] | no | Evidence types/commands |
| `hypothesis_seeds` | string[] | no | Initial hypothesis templates |
| `verification_steps` | object[] | yes | Verification checklist |
| `status` | enum | yes | draft, active, deprecated |

### Relationships

- Referenced by: Case
- Contains references to: KnowledgeItem[]
- Used by: Investigation Planner, Question Engine, Evidence Engine

### Example YAML

```yaml
playbook_id: VP-CUBE-0001
version: "1.0"
vendor: cisco
category: cube
title: Outbound Calls Fail
symptoms:
  - outbound PSTN failure
  - fast busy
  - SIP 404 403 408 488 503
applicability:
  platforms: [cisco_cube]
  topology_patterns: [cucm_cube_itsp, cube_itsp]
  required_components: [cube]
phases:
  intake:
    questions: [QST-template-001, QST-template-002]
  collection:
    required_commands:
      - show dial-peer voice summary
      - show sip-ua status
      - debug ccsip messages
  verification:
    steps:
      - test_local_outbound
      - test_mobile_outbound
hypothesis_seeds:
  - dial-peer mismatch
  - provider rejection
  - trunk down
status: active
```

---

## 18. Knowledge Item Object

### Purpose

A Knowledge Item is a curated reference fact, rule, or pattern from the Knowledge Engine corpus.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `knowledge_item_id` | string | yes | `KNW-{uuid}` |
| `domain` | enum | yes | cisco, microsoft, sip, rtp, security, playbook, rfc |
| `type` | enum | yes | rule, interpretation, command, bug, compatibility, best_practice |
| `title` | string | yes | Short title |
| `content` | string | yes | Knowledge body |
| `applicability` | object | no | platforms, versions, symptoms |
| `source` | object | yes | document, author, review_date |
| `effective_from` | date | no | Validity start |
| `deprecated` | boolean | yes | Deprecation flag |
| `superseded_by` | string | no | Replacement knowledge_item_id |

### Relationships

- Referenced by: Hypothesis, ParserFinding, Playbook, Decision
- Produced by: Learning Engine (after review)

### Example YAML

```yaml
knowledge_item_id: KNW-cube-local-404
domain: cisco
type: interpretation
title: Local 404 on CUBE indicates routing issue
content: SIP 404 with local response origin on CUBE typically indicates dial-peer mismatch or translation failure, not provider rejection.
applicability:
  platforms: [cisco_cube]
  symptoms: [outbound_failure, sip_404]
source:
  document: VP-CUBE-0001
  author: voicepilot-curator
  review_date: 2026-06-01
deprecated: false
```

---

## 19. Confidence Score Object

### Purpose

A Confidence Score is a point-in-time, explainable assessment of investigation certainty.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `confidence_score_id` | string | yes | `CONF-{uuid}` |
| `case_id` | string | yes | Parent case |
| `score` | number | yes | 0–100 |
| `explanation` | string | yes | Human-readable rationale |
| `factors` | object[] | yes | factor, weight, value, contribution |
| `trend` | enum | no | rising, stable, falling, volatile |
| `gate_results` | object[] | no | gate_name, threshold, passed |
| `trigger_event` | string | no | What caused recalculation |
| `calculated_at` | datetime | yes | Timestamp |
| `calculated_by` | string | yes | confidence-engine |

### Relationships

- Belongs to: Case
- Informs: Decision, Recommendation
- Referenced by: Report

### Example YAML

```yaml
confidence_score_id: CONF-008
case_id: CASE-7f3a2b1c
score: 92
explanation: Leading hypothesis supported by local 404 and dial-peer config gap. Trunk up. No contradicting evidence. Verification pending.
factors:
  - factor: evidence_coverage
    weight: 0.30
    value: 0.95
    contribution: 28.5
  - factor: hypothesis_discrimination
    weight: 0.25
    value: 0.90
    contribution: 22.5
  - factor: evidence_quality
    weight: 0.25
    value: 0.87
    contribution: 21.75
trend: rising
gate_results:
  - gate_name: root_cause_declare
    threshold: 85
    passed: true
calculated_at: 2026-06-19T11:45:00Z
calculated_by: confidence-engine
```

---

## 20. Recommendation Object

### Purpose

A Recommendation proposes the next investigative action with cost, gain, verification, and rollback guidance.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recommendation_id` | string | yes | `REC-{uuid}` |
| `case_id` | string | yes | Parent case |
| `action_type` | enum | yes | ask_question, collect_evidence, run_test, apply_fix |
| `description` | string | yes | What to do |
| `rationale` | string | yes | Why this action |
| `cost_level` | enum | yes | low, medium, high, critical |
| `information_gain` | number | yes | Expected value 0–1 |
| `priority_rank` | integer | yes | Rank among candidates |
| `target_device_id` | string | no | Device target |
| `command` | string | no | CLI if applicable |
| `verification_steps` | string[] | no | How to confirm action outcome |
| `rollback_steps` | string[] | no* | *Required for high/critical |
| `requires_engineer_approval` | boolean | yes | Approval gate |
| `status` | enum | yes | recommended, approved, rejected, completed |
| `investigation_step_id` | string | no | Created step if executed |

### Relationships

- Belongs to: Case
- Creates: InvestigationStep
- Produced by: Cost Optimizer, Investigation Planner

### Example YAML

```yaml
recommendation_id: REC-003
case_id: CASE-7f3a2b1c
action_type: collect_evidence
description: Collect CUBE dial-peer configuration
rationale: High discrimination for dial-peer mismatch hypothesis; low operational cost
cost_level: low
information_gain: 0.82
priority_rank: 1
target_device_id: DEV-cube-01
command: show run | sec dial-peer
verification_steps:
  - Confirm output contains all outbound dial-peers
rollback_steps: []
requires_engineer_approval: false
status: completed
investigation_step_id: STEP-004
```

---

## 21. Verification Object

### Purpose

A Verification records a post-resolution test and its outcome against the playbook checklist.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_id` | string | yes | `VER-{uuid}` |
| `case_id` | string | yes | Parent case |
| `step_name` | string | yes | Checklist step identifier |
| `description` | string | yes | What was tested |
| `expected_result` | string | yes | Pass criteria |
| `actual_result` | string | yes | Observed outcome |
| `passed` | boolean | yes | Pass/fail |
| `evidence_id` | string | no | Supporting test evidence |
| `executed_at` | datetime | yes | Test time |
| `executed_by` | string | yes | Engineer identity |
| `playbook_id` | string | no | Source playbook step |

### Relationships

- Belongs to: Case
- References: Evidence, Playbook
- Node in: InvestigationGraph

### Example YAML

```yaml
verification_id: VER-002
case_id: CASE-7f3a2b1c
step_name: test_mobile_outbound
description: Place outbound call to mobile number
expected_result: Call connects with two-way audio
actual_result: Call connected successfully to +15551234567
passed: true
evidence_id: EVD-007
executed_at: 2026-06-19T12:20:00Z
executed_by: engineer@example.com
playbook_id: VP-CUBE-0001
```

---

## 22. Report Object

### Purpose

A Report is a generated investigation deliverable with versioned content and citation index.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_id` | string | yes | `RPT-{uuid}` |
| `case_id` | string | yes | Parent case |
| `type` | enum | yes | incident_summary, rca, executive, technical, closure |
| `version` | integer | yes | Report version |
| `status` | enum | yes | draft, final |
| `sections` | object[] | yes | section_id, title, content_ref |
| `citation_index` | object[] | yes | claim, evidence_ids, decision_ids |
| `generated_at` | datetime | yes | Generation time |
| `generated_by` | string | yes | report-engine |

### Relationships

- Belongs to: Case
- References: Evidence[], Decision[], ConfidenceScore, Verification[]

### Example YAML

```yaml
report_id: RPT-001
case_id: CASE-7f3a2b1c
type: closure
version: 1
status: final
sections:
  - section_id: executive_summary
    title: Executive Summary
    content_ref: report-store://RPT-001/executive_summary
  - section_id: root_cause_analysis
    title: Root Cause Analysis
    content_ref: report-store://RPT-001/rca
citation_index:
  - claim: Root cause is missing mobile dial-peer on CUBE
    evidence_ids: [EVD-002, EVD-005]
    decision_ids: [DEC-006]
generated_at: 2026-06-19T12:45:00Z
generated_by: report-engine
```

---

## 23. Learning Record Object

### Purpose

A Learning Record is an anonymized, structured knowledge artifact derived from a closed case.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `learning_record_id` | string | yes | `LRN-{uuid}` |
| `source_case_id` | string | yes | Internal lineage only |
| `anonymized` | boolean | yes | Must be true for publication |
| `symptoms` | string[] | yes | Symptom patterns |
| `topology_pattern` | string | yes | e.g., cucm_cube_itsp |
| `platforms` | string[] | yes | Platform types |
| `evidence_signatures` | object[] | yes | signal_type, signal_value patterns |
| `root_cause_category` | string | yes | Category |
| `root_cause_summary` | string | yes | Anonymized description |
| `resolution_summary` | string | yes | Fix pattern |
| `verification_passed` | boolean | yes | First-pass verification |
| `lessons_learned` | string[] | yes | Structured lessons |
| `playbook_id` | string | no | Source playbook |
| `confidence_at_closure` | number | yes | Final confidence |
| `review_status` | enum | yes | pending, approved, rejected |
| `captured_at` | datetime | yes | Creation time |

### Relationships

- Derived from: Case (anonymized)
- Indexed in: Knowledge Engine
- Compared by: Investigation Graph (similarity)

### Example YAML

```yaml
learning_record_id: LRN-0042
source_case_id: CASE-7f3a2b1c
anonymized: true
symptoms: [outbound_pstn_failure, fast_busy, local_sip_404]
topology_pattern: cucm_cube_itsp
platforms: [cisco_cucm, cisco_cube]
evidence_signatures:
  - signal_type: sip_response_code
    signal_value: "404"
    context: response_origin_local
root_cause_category: routing
root_cause_summary: Missing dial-peer for mobile prefix after configuration change
resolution_summary: Added dial-peer covering mobile number pattern
verification_passed: true
lessons_learned:
  - Validate all destination classes after dial-peer edits
playbook_id: VP-CUBE-0001
confidence_at_closure: 92
review_status: approved
captured_at: 2026-06-19T13:00:00Z
```

---

## 24. Investigation Graph Object

### Purpose

The Investigation Graph stores typed nodes and edges representing investigation reasoning for a case.

### Key Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `graph_id` | string | yes | `GRPH-{uuid}` |
| `case_id` | string | yes | Parent case |
| `nodes` | object[] | yes | node_id, type, entity_ref, attributes |
| `edges` | object[] | yes | edge_id, from, to, type, confidence |
| `schema_version` | string | yes | Graph schema version |
| `snapshot_version` | integer | yes | Increments on milestone snapshot |
| `updated_at` | datetime | yes | Last mutation |

### Relationships

- Belongs to: Case
- Nodes reference: all Case-scoped entity types
- Used by: Reasoning Engine, Confidence Engine, Report Engine, Learning Engine

### Example YAML

```yaml
graph_id: GRPH-001
case_id: CASE-7f3a2b1c
nodes:
  - node_id: N-001
    type: symptom
    entity_ref: case.symptom
  - node_id: N-002
    type: evidence
    entity_ref: EVD-002
  - node_id: N-003
    type: hypothesis
    entity_ref: HYP-dp-001
  - node_id: N-004
    type: decision
    entity_ref: DEC-006
edges:
  - edge_id: E-001
    from: N-002
    to: N-003
    type: supports
    confidence: 0.91
  - edge_id: E-002
    from: N-004
    to: N-003
    type: confirms
    confidence: 0.92
schema_version: "1.0"
snapshot_version: 3
updated_at: 2026-06-19T11:45:00Z
```

---

## 25. MVP Example: VP-CUBE-0001 Outbound Calls Fail

**Scenario:** Cisco CUCM → Cisco CUBE → ITSP. All outbound PSTN calls fail.

### Object Instances Created

| Phase | Objects |
|-------|---------|
| Case Open | Case, Playbook ref (VP-CUBE-0001), TimelineEvent (case_opened) |
| Intake | Question ×3, TimelineEvent (intake_completed), Decision (strategy routing-first) |
| Topology | Topology, Device ×3 (CUCM, CUBE, ITSP), TimelineEvent (topology_identified) |
| Collection | LogArtifact, Evidence (sip-ua status), Evidence (SIP debug), ParserFinding (local 404), Configuration, Evidence (dial-peer config) |
| Analysis | Hypothesis ×4, InvestigationGraph nodes/edges |
| Investigation | Decision ×3 (eliminations), Recommendation, InvestigationStep, Question (mobile-only) |
| Resolution | Hypothesis (confirmed), Decision (root cause), ConfidenceScore (92, gate pass) |
| Verification | Verification ×3, Evidence (test results) |
| Closure | Report (closure), LearningRecord (anonymized), TimelineEvent (case_closed) |

### Root Cause Confirmation Chain

```
LOG-002 → EVD-002 → FIND-001 (local 404)
CFG-005 → EVD-005 → FIND-003 (mobile peer gap)
         ↓
    HYP-dp-001 (confirmed)
         ↓
    DEC-006 (confirmation) + CONF-008 (gate pass)
         ↓
    Case.root_cause_id = HYP-dp-001
```

### Data Model Validation

- Root cause confirmed only with `supporting_evidence_ids` populated on HYP-dp-001
- DEC-006 includes `alternatives_considered` with rejection reasons
- REC-003 for dial-peer collection includes `cost_level: low` and empty `rollback_steps` (read-only)
- CONF-008 includes `factors` and `explanation` for audit
- LearningRecord has `anonymized: true` before Knowledge Engine indexing

---

## 26. Future Database Mapping

| Canonical Object | Suggested Store | Notes |
|------------------|-----------------|-------|
| Case | Relational primary table + JSONB extensions | Partition by tenant; status indexed |
| Evidence, LogArtifact, Configuration | Relational + blob store | `content_ref` points to object storage |
| Hypothesis, Decision, Question | Relational child tables | Foreign key to case_id; append-only for Decision |
| TimelineEvent | Event table or event stream | Append-only; sequence indexed |
| Topology, Device | Relational + graph optional | JSONB for relationships |
| ParserFinding | Relational child of Evidence | Indexed by signal_type |
| Playbook, KnowledgeItem | CMS / knowledge tables | Versioned; effective date indexing |
| ConfidenceScore | Time-series friendly table | Multiple rows per case |
| Recommendation, InvestigationStep | Relational workflow tables | Status transitions audited |
| Verification, Report | Relational + blob for sections | Report immutable when final |
| LearningRecord | Anonymized analytics store | Separated from PII case store |
| InvestigationGraph | Graph DB or JSONB document | Neo4j/JanusGraph optional for similarity queries |

**Tenancy:** All tables include `tenant_id`. Case store and Learning store may be physically separated.

**Audit:** `created_at`, `created_by`, `updated_at`, `updated_by` on all mutable tables. Decision and TimelineEvent are append-only.

---

## 27. Future API Mapping

| Operation | Resource | Method (conceptual) | Notes |
|-----------|----------|---------------------|-------|
| Open case | `/cases` | POST | Returns Case |
| Get case | `/cases/{case_id}` | GET | Full aggregate or field selection |
| Add evidence | `/cases/{case_id}/evidence` | POST | Accepts artifact upload + metadata |
| List hypotheses | `/cases/{case_id}/hypotheses` | GET | Ranked list |
| Record decision | `/cases/{case_id}/decisions` | POST | Append-only |
| Next recommendation | `/cases/{case_id}/recommendations/next` | GET | Top ranked action |
| Approve recommendation | `/cases/{case_id}/recommendations/{id}/approve` | POST | Engineer control |
| Confidence snapshot | `/cases/{case_id}/confidence` | GET | Latest score + explanation |
| Timeline | `/cases/{case_id}/timeline` | GET | Ordered events |
| Graph | `/cases/{case_id}/graph` | GET | Nodes and edges |
| Verification | `/cases/{case_id}/verifications` | POST | Test results |
| Report | `/cases/{case_id}/reports/{type}` | GET | Generated deliverable |

**API principles:** RESTful resources map 1:1 to canonical objects. No free-text conclusion endpoints — root cause via Decision + Hypothesis confirmation only. ETags on Case for optimistic concurrency.

---

## 28. Future AI Agent Mapping

| Agent | Primary Objects Read | Primary Objects Write |
|-------|---------------------|----------------------|
| Intake Agent | Case, Playbook, Question | Case, Question, TimelineEvent |
| Topology Agent | Case, Topology, Device, KnowledgeItem | Topology, Device, Question |
| Evidence Agent | Case, Recommendation, InvestigationStep, Device | LogArtifact, Configuration, Evidence, ParserFinding |
| Hypothesis Agent | Case, Evidence, ParserFinding, KnowledgeItem, InvestigationGraph | Hypothesis, InvestigationGraph |
| Decision Agent | Hypothesis, Evidence, ConfidenceScore | Decision, TimelineEvent |
| Question Agent | Case, Hypothesis, Topology, Playbook | Question, Recommendation |
| Solution Agent | Hypothesis, Evidence, Playbook, Recommendation | Recommendation, InvestigationStep |
| Verification Agent | Case, Playbook, Verification | Verification, Evidence |
| Report Agent | Case, all child objects | Report |
| Learning Agent | Case, Report, InvestigationGraph | LearningRecord |

**Agent rule:** Agents mutate canonical objects only. Conversation layer translates user input into object operations. No agent writes `root_cause` directly — must create Decision (confirmation) + Hypothesis (confirmed) with evidence links, passing Confidence gate.

---

*VoicePilot Canonical Data Model v1.0 — Sprint 0, Day 3*
*Review status: Draft for Distinguished Engineer review*
