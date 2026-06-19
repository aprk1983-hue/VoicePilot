# VoicePilot DSL Specification

**Version:** 1.0.0-draft  
**Status:** Architecture specification — Sprint 0, Day 4  
**File extension:** `.vpb.yaml` (VoicePilot Playbook)

---

## 1. Purpose

The VoicePilot Domain Specific Language (DSL) defines a structured, YAML-based format for authoring investigation playbooks. Playbooks written in this DSL are the declarative source of truth for how VoicePilot investigates a class of voice incidents — from intake questions through evidence collection, hypothesis evaluation, confidence gating, resolution, verification, and learning capture.

The DSL is not a chat script. It is an operational specification that a senior TAC engineer would recognize as a formal investigation procedure with explicit rules, not conversational prompts.

---

## 2. Why VoicePilot Needs a DSL

| Problem Without DSL | DSL Solution |
|---------------------|--------------|
| Playbooks as prose markdown | Machine-readable rules engines can execute deterministically |
| Inconsistent investigation depth across scenarios | Required fields enforce TAC discipline per scenario |
| Logic buried in engine code | Evidence, confidence, and decision rules live with the playbook |
| Vendor logic scattered across services | Platform-specific commands and parsers declared in one artifact |
| Hard to version and audit | Semantic versioning with validation rules |
| Difficult to compare playbooks | Uniform structure enables diff, review, and SME approval workflows |

VoicePilot engines interpret DSL playbooks at runtime. Engineers author playbooks; engines execute them against live Case objects.

---

## 3. Design Principles

| Principle | Description |
|-----------|-------------|
| Declarative Over Imperative | Playbooks declare what to investigate, not how engines implement it |
| Evidence-First | No confirmation rule without evidence conditions |
| Never Guess | Hypothesis and decision rules require explicit signals |
| Engineer in Control | Critical actions declare `requires_approval: true` |
| Vendor-Neutral Schema | Platform specifics in `platforms` and `extensions`, not schema forks |
| Composable Rules | Rules reference IDs; engines evaluate against canonical objects |
| Cost-Aware | Every collection action declares operational cost |
| Auditable | Playbook version bound to Case; rule evaluations logged in Decision Engine |
| Validatable | Playbooks must pass schema validation before publication |
| Canonical Mapping | Every DSL block maps to one or more canonical data model objects |

---

## 4. DSL Object Structure

A VoicePilot playbook is a single YAML document with a root `playbook` key:

```yaml
playbook:
  api_version: voicepilot.io/v1
  kind: Playbook

  metadata: { ... }
  platforms: [ ... ]
  symptoms: [ ... ]
  business_impact: { ... }
  topology: { ... }
  intake: { ... }
  evidence: { ... }
  parsers: { ... }
  hypotheses: [ ... ]
  rules:
    evidence: [ ... ]
    confidence: [ ... ]
    decision: [ ... ]
    next_best_action: [ ... ]
  cost_model: { ... }
  resolution: [ ... ]
  verification: [ ... ]
  rollback: [ ... ]
  preventive_actions: [ ... ]
  report: { ... }
  learning: { ... }
  strategies: [ ... ]          # optional
  extensions: { ... }          # optional
```

---

## 5. Required Fields

| Path | Description |
|------|-------------|
| `playbook.api_version` | DSL API version |
| `playbook.kind` | Must be `Playbook` |
| `playbook.metadata.id` | Unique playbook ID (e.g., `VP-CUBE-0001`) |
| `playbook.metadata.version` | Semantic version |
| `playbook.metadata.title` | Human-readable title |
| `playbook.metadata.status` | `draft`, `active`, or `deprecated` |
| `playbook.platforms` | At least one supported platform |
| `playbook.symptoms` | At least one symptom matcher |
| `playbook.business_impact` | Impact classification |
| `playbook.topology` | Required topology pattern |
| `playbook.intake.questions` | At least one intake question |
| `playbook.evidence.requirements` | At least one evidence requirement |
| `playbook.hypotheses` | At least one hypothesis seed |
| `playbook.rules.evidence` | At least one evidence interpretation rule |
| `playbook.rules.confidence` | At least one confidence gate |
| `playbook.verification.steps` | At least one verification step |
| `playbook.report.sections` | At least one report section |
| `playbook.learning.capture_fields` | At least one learning field |

---

## 6. Optional Fields

| Path | Description |
|------|-------------|
| `playbook.metadata.author` | Playbook author |
| `playbook.metadata.reviewed_by` | SME reviewer |
| `playbook.metadata.tags` | Search tags |
| `playbook.metadata.related_playbooks` | Related playbook IDs |
| `playbook.strategies` | Investigation strategy hints for Investigation Planner |
| `playbook.rules.decision` | Auto-decision rules (elimination templates) |
| `playbook.rules.next_best_action` | Action selection overrides |
| `playbook.cost_model` | Custom cost overrides |
| `playbook.resolution` | Resolution step templates |
| `playbook.rollback` | Rollback guidance for risky steps |
| `playbook.preventive_actions` | Post-incident prevention templates |
| `playbook.parsers` | Parser finding extraction definitions |
| `playbook.extensions` | Vendor-specific opaque metadata |

---

## 7. Field Definitions

### 7.1 Metadata

```yaml
metadata:
  id: VP-CUBE-0001
  version: "1.0.0"
  title: Outbound Calls Fail
  description: Investigation for outbound PSTN failure on Cisco CUBE
  category: cube
  vendor: cisco
  status: active
  author: voicepilot-curator
  reviewed_by: tac-sme
  effective_from: 2026-06-01
  tags: [outbound, pstn, cube, sip]
  related_playbooks: []
```

### 7.2 Supported Platforms

```yaml
platforms:
  - vendor: cisco
    products: [cube, ios_voice]
    min_version: "15.0"
    max_version: null
    roles: [session_border]
```

### 7.3 Symptoms

```yaml
symptoms:
  - id: SYM-001
    match:
      summary_contains: [outbound, PSTN, external]
      failure_modes: [fast_busy, no_dial_tone, immediate_disconnect]
      sip_codes: [404, 403, 408, 488, 503]
    weight: 1.0
```

### 7.4 Business Impact

```yaml
business_impact:
  default_severity: high
  description: Users cannot place outbound PSTN calls
  escalation_threshold_minutes: 60
  user_impact: external_calling_blocked
```

### 7.5 Required Topology

```yaml
topology:
  pattern: cucm_cube_itsp
  required_components:
    - type: cube
      role: session_border
      min_count: 1
  optional_components:
    - type: cucm
      role: call_manager
  path:
    signaling: [cucm, cube, provider]
    media: [cucm, cube, provider]
```

### 7.6 Intake Questions

```yaml
intake:
  questions:
    - id: Q-INT-001
      text: Did outbound PSTN calling ever work in this environment?
      category: intake
      phase: INTAKE
      target_field: known_facts.worked_previously
      required: true
      information_gain: 0.85
    - id: Q-INT-002
      text: Were any changes made to CUBE, CUCM, or the provider recently?
      category: change
      phase: INTAKE
      target_field: recent_changes
      required: true
      information_gain: 0.90
```

### 7.7 Evidence Requirements

```yaml
evidence:
  requirements:
    - id: EVD-REQ-001
      title: SIP UA registration status
      type: cli_output
      mandatory: true
      phase: COLLECTION
      blocks_confirmation: true
    - id: EVD-REQ-002
      title: SIP debug for failing call
      type: debug_log
      mandatory: true
      phase: COLLECTION
      blocks_confirmation: true
    - id: EVD-REQ-003
      title: Dial-peer configuration
      type: config_excerpt
      mandatory: true
      phase: COLLECTION
      blocks_confirmation: true
```

### 7.8 Commands to Collect

```yaml
evidence:
  commands:
    - id: CMD-001
      requirement_id: EVD-REQ-001
      device_role: session_border
      command: show sip-ua status
      cost: low
      privilege: show
    - id: CMD-002
      requirement_id: EVD-REQ-003
      device_role: session_border
      command: show run | sec dial-peer
      cost: low
      privilege: show
    - id: CMD-003
      device_role: session_border
      command: show dial-peer voice summary
      cost: low
      optional: true
```

### 7.9 Log Artifacts

```yaml
evidence:
  logs:
    - id: LOG-REQ-001
      requirement_id: EVD-REQ-002
      log_type: sip_trace
      device_role: session_border
      command: debug ccsip messages
      cost: medium
      guidance: Capture one failing outbound call attempt
      requires_approval: false
```

### 7.10 Parser Findings

```yaml
parsers:
  findings:
    - id: PARSE-001
      applies_to: [sip_trace]
      signal_type: sip_response_code
      extract:
        pattern: 'SIP/2.0 (?P<code>\d{3})'
      emit_finding: FIND-SIP-CODE
    - id: PARSE-002
      applies_to: [sip_trace]
      signal_type: response_origin
      extract:
        pattern: 'response origin: (?P<origin>local|remote)'
      emit_finding: FIND-RESP-ORIGIN
```

### 7.11 Hypotheses

```yaml
hypotheses:
  - id: HYP-DP-001
    title: CUBE dial-peer mismatch
    category: routing
    initial_status: candidate
    default_rank: 1
    affected_components: [cube]
  - id: HYP-TRUNK-001
    title: SIP trunk down or unregistered
    category: provider
    initial_status: candidate
    default_rank: 2
  - id: HYP-PROVIDER-001
    title: Provider-side rejection
    category: provider
    initial_status: candidate
    default_rank: 3
  - id: HYP-CODEC-001
    title: Codec or SDP mismatch
    category: media
    initial_status: candidate
    default_rank: 4
```

### 7.12–7.15 Rules

See sections 8–11 for rule syntax.

### 7.16 Cost Model

```yaml
cost_model:
  defaults:
    ask_question: low
    show_command: low
    debug_log: medium
    packet_capture: high
    service_restart: critical
    config_change: critical
  overrides:
    - command_id: CMD-DEBUG-001
      cost: medium
      requires_approval: false
```

### 7.17 Resolution Steps

```yaml
resolution:
  - id: RES-001
    title: Correct dial-peer configuration
    description: Add or correct dial-peer covering failing destination class
    applies_to_hypothesis: HYP-DP-001
    verification_required: true
    requires_approval: true
    rollback_ref: RBK-001
```

### 7.18 Verification Steps

```yaml
verification:
  steps:
    - id: VER-001
      name: test_local_outbound
      description: Place outbound call to local landline
      expected: Call connects with two-way audio
      mandatory: true
    - id: VER-002
      name: test_mobile_outbound
      description: Place outbound call to mobile number
      expected: Call connects with two-way audio
      mandatory: true
```

### 7.19 Rollback Guidance

```yaml
rollback:
  - id: RBK-001
    applies_to: RES-001
    description: Restore previous dial-peer configuration from backup
    steps:
      - Restore dial-peer config from last known good
      - Run show dial-peer voice summary to confirm
    requires_approval: true
```

### 7.20 Preventive Actions

```yaml
preventive_actions:
  - id: PREV-001
    title: Dial-peer change checklist
    description: Validate all destination classes after dial-peer edits
  - id: PREV-002
    title: Post-change test script
    description: Run local, mobile, and international test calls after CUBE changes
```

### 7.21 Report Sections

```yaml
report:
  sections:
    - id: executive_summary
      title: Executive Summary
      required: true
    - id: root_cause_analysis
      title: Root Cause Analysis
      required: true
    - id: evidence_appendix
      title: Evidence Appendix
      required: true
    - id: elimination_narrative
      title: Hypothesis Elimination
      required: true
```

### 7.22 Learning Fields

```yaml
learning:
  capture_fields:
    - symptoms
    - topology_pattern
    - evidence_signatures
    - root_cause_category
    - resolution_summary
    - lessons_learned
  anonymize:
    - hostname
    - ip_address
    - phone_number
    - customer_name
  lesson_templates:
    - After dial-peer edits, validate all destination classes including mobile
```

---

## 8. Confidence Rule Syntax

Confidence rules define gates and scoring adjustments evaluated by the Confidence Engine.

```yaml
rules:
  confidence:
    gates:
      - id: CONF-GATE-ROOT
        name: root_cause_declare
        threshold: 85
        requires:
          - all_mandatory_evidence_collected
          - leading_hypothesis_has_supporting_evidence
          - no_active_contradicting_evidence
        blocks: RESOLUTION

      - id: CONF-GATE-CLOSE
        name: case_close
        threshold: 80
        requires:
          - all_mandatory_verification_passed
        blocks: CLOSED

    adjustments:
      - id: CONF-ADJ-001
        when:
          finding: FIND-RESP-ORIGIN
          equals: local
        boost_hypothesis: HYP-DP-001
        score_delta: 15
        reason: Local SIP response origin indicates CUBE routing issue

      - id: CONF-ADJ-002
        when:
          finding: FIND-SIP-CODE
          equals: "503"
          and:
            finding: FIND-RESP-ORIGIN
            equals: remote
        boost_hypothesis: HYP-PROVIDER-001
        score_delta: 20
        reason: Remote 503 suggests provider rejection
```

**Gate evaluation:** All `requires` conditions must pass AND `score >= threshold`.

---

## 9. Evidence Rule Syntax

Evidence rules map parser findings and signals to hypothesis support, contradiction, or elimination hints.

```yaml
rules:
  evidence:
    - id: EV-RULE-001
      name: local_404_routing
      when:
        all:
          - finding: FIND-SIP-CODE
            equals: "404"
          - finding: FIND-RESP-ORIGIN
            equals: local
      supports: [HYP-DP-001]
      contradicts: [HYP-PROVIDER-001]
      knowledge_ref: KNW-cube-local-404
      interpretation: Local 404 on CUBE indicates dial-peer or routing issue

    - id: EV-RULE-002
      name: trunk_registered
      when:
        signal_type: registration_state
        equals: registered
      contradicts: [HYP-TRUNK-001]

    - id: EV-RULE-003
      name: codec_mismatch_488
      when:
        finding: FIND-SIP-CODE
        equals: "488"
      supports: [HYP-CODEC-001]

    - id: EV-RULE-004
      name: timeout_408
      when:
        finding: FIND-SIP-CODE
        equals: "408"
      supports: [HYP-NETWORK-001]
      strategy_hint: network-first
```

**Condition operators:** `equals`, `in`, `matches` (regex), `all`, `any`, `not`.

---

## 10. Question Rule Syntax

Question rules govern dynamic question selection beyond static intake.

```yaml
rules:
  questions:
    - id: Q-RULE-001
      when:
        phase: INVESTIGATION
        hypothesis_active: HYP-DP-001
        fact_missing: affected_scope.destination_classes
      ask: Q-DISC-001
      priority: 1

    - id: Q-RULE-002
      when:
        phase: TOPOLOGY
        topology_gap: provider
      ask: Q-TOPO-001
      priority: 1

  question_bank:
    - id: Q-DISC-001
      text: Are failing calls limited to mobile numbers, or also landline?
      category: discrimination
      target_field: affected_scope.destination_classes
      information_gain: 0.88
      discriminates: [HYP-DP-001, HYP-PROVIDER-001]

    - id: Q-TOPO-001
      text: Which ITSP/SIP provider carries outbound PSTN for this site?
      category: topology
      target_field: topology.provider
      information_gain: 0.75
```

---

## 11. Cost Model Syntax

```yaml
cost_model:
  levels:
    low:
      multiplier: 1
      requires_approval: false
    medium:
      multiplier: 3
      requires_approval: false
    high:
      multiplier: 8
      requires_approval: true
    critical:
      multiplier: 25
      requires_approval: true

  action_types:
    ask_question: low
    show_command: low
    debug_log: medium
    packet_capture: high
    service_restart: critical
    config_change: critical

  selection:
    prefer_lower_cost: true
    minimum_information_gain: 0.3
    defer_above: high
    block_without_approval: critical
```

---

## 12. Example Full DSL: VP-CUBE-0001 Outbound Calls Fail

```yaml
playbook:
  api_version: voicepilot.io/v1
  kind: Playbook

  metadata:
    id: VP-CUBE-0001
    version: "1.0.0"
    title: Outbound Calls Fail
    description: Investigation playbook for outbound PSTN failure on Cisco CUBE
    category: cube
    vendor: cisco
    status: active
    author: voicepilot-curator
    reviewed_by: tac-sme
    tags: [outbound, pstn, cube, sip, routing]
    effective_from: 2026-06-01

  platforms:
    - vendor: cisco
      products: [cube]
      roles: [session_border]

  symptoms:
    - id: SYM-OUTBOUND-FAIL
      match:
        summary_contains: [outbound, PSTN, external]
        failure_modes: [fast_busy, no_dial_tone]
        sip_codes: [404, 403, 408, 488, 503]
      weight: 1.0

  business_impact:
    default_severity: high
    description: Users cannot call external PSTN numbers
    escalation_threshold_minutes: 60

  topology:
    pattern: cucm_cube_itsp
    required_components:
      - type: cube
        role: session_border
        min_count: 1
    path:
      signaling: [cucm, cube, provider]

  strategies:
    - id: routing-first
      weight: 0.85
      when:
        sip_codes_present: [404]
    - id: change-first
      weight: 0.70
      when:
        recent_change_reported: true

  intake:
    questions:
      - id: Q-INT-001
        text: Did outbound PSTN calling ever work in this environment?
        category: intake
        phase: INTAKE
        target_field: known_facts.worked_previously
        required: true
        information_gain: 0.85
      - id: Q-INT-002
        text: When did outbound calling stop working?
        category: intake
        phase: INTAKE
        target_field: timeline.onset
        required: true
        information_gain: 0.80
      - id: Q-INT-003
        text: Were any changes made to CUBE, CUCM, or the provider recently?
        category: change
        phase: INTAKE
        target_field: recent_changes
        required: true
        information_gain: 0.90
      - id: Q-INT-004
        text: Are all outbound calls failing, or only specific destinations?
        category: scope
        phase: INTAKE
        target_field: affected_scope.destination_classes
        required: true
        information_gain: 0.88
      - id: Q-INT-005
        text: Are inbound PSTN calls still working?
        category: scope
        phase: INTAKE
        target_field: known_facts.inbound_working
        required: false
        information_gain: 0.60
      - id: Q-INT-006
        text: Which ITSP/SIP provider carries outbound PSTN?
        category: topology
        phase: DISCOVERY
        target_field: topology.provider
        required: true
        information_gain: 0.75

  evidence:
    requirements:
      - id: EVD-REQ-SIP-UA
        title: SIP UA registration status
        type: cli_output
        mandatory: true
        phase: COLLECTION
        blocks_confirmation: true
      - id: EVD-REQ-SIP-DEBUG
        title: SIP debug for failing call
        type: debug_log
        mandatory: true
        phase: COLLECTION
        blocks_confirmation: true
      - id: EVD-REQ-DIAL-PEER
        title: Dial-peer configuration
        type: config_excerpt
        mandatory: true
        phase: COLLECTION
        blocks_confirmation: true

    commands:
      - id: CMD-SIP-UA
        requirement_id: EVD-REQ-SIP-UA
        device_role: session_border
        command: show sip-ua status
        cost: low
      - id: CMD-DIAL-PEER-SUM
        device_role: session_border
        command: show dial-peer voice summary
        cost: low
        optional: true
      - id: CMD-DIAL-PEER-RUN
        requirement_id: EVD-REQ-DIAL-PEER
        device_role: session_border
        command: show run | sec dial-peer
        cost: low
      - id: CMD-VOICE-SVC
        device_role: session_border
        command: show run | sec voice service voip
        cost: low
        optional: true
      - id: CMD-CALL-ACTIVE
        device_role: session_border
        command: show call active voice brief
        cost: low
        optional: true
      - id: CMD-LOGGING
        device_role: session_border
        command: show logging
        cost: low
        optional: true

    logs:
      - id: LOG-SIP-DEBUG
        requirement_id: EVD-REQ-SIP-DEBUG
        log_type: sip_trace
        device_role: session_border
        command: debug ccsip messages
        cost: medium
        guidance: Capture debug during one failing outbound call attempt

  parsers:
    findings:
      - id: PARSE-SIP-CODE
        applies_to: [sip_trace]
        signal_type: sip_response_code
        extract:
          pattern: 'SIP/2.0 (?P<code>\d{3})'
        emit_finding: FIND-SIP-CODE
      - id: PARSE-RESP-ORIGIN
        applies_to: [sip_trace]
        signal_type: response_origin
        extract:
          pattern: '(?i)(local|remote)'
        emit_finding: FIND-RESP-ORIGIN
      - id: PARSE-REG-STATE
        applies_to: [cli_output]
        signal_type: registration_state
        extract:
          pattern: 'Status.*(UP|DOWN|REGISTERED)'
        emit_finding: FIND-REG-STATE

  hypotheses:
    - id: HYP-DP-001
      title: CUBE dial-peer mismatch
      category: routing
      initial_status: candidate
      default_rank: 1
    - id: HYP-TRUNK-001
      title: SIP trunk down or unregistered
      category: provider
      initial_status: candidate
      default_rank: 2
    - id: HYP-PROVIDER-001
      title: Provider-side rejection
      category: provider
      initial_status: candidate
      default_rank: 3
    - id: HYP-TRANS-001
      title: Translation rule issue
      category: routing
      initial_status: candidate
      default_rank: 4
    - id: HYP-CODEC-001
      title: Codec or SDP mismatch
      category: media
      initial_status: candidate
      default_rank: 5
    - id: HYP-NETWORK-001
      title: Firewall, DNS, or network timeout
      category: network
      initial_status: candidate
      default_rank: 6
    - id: HYP-TLS-001
      title: TLS or certificate issue
      category: security
      initial_status: candidate
      default_rank: 7

  rules:
    evidence:
      - id: EV-RULE-LOCAL-404
        when:
          all:
            - finding: FIND-SIP-CODE
              equals: "404"
            - finding: FIND-RESP-ORIGIN
              equals: local
        supports: [HYP-DP-001, HYP-TRANS-001]
        contradicts: [HYP-PROVIDER-001]
        interpretation: Local 404 indicates CUBE routing/dial-peer issue

      - id: EV-RULE-TRUNK-UP
        when:
          finding: FIND-REG-STATE
          in: [UP, REGISTERED]
        contradicts: [HYP-TRUNK-001]

      - id: EV-RULE-488
        when:
          finding: FIND-SIP-CODE
          equals: "488"
        supports: [HYP-CODEC-001]

      - id: EV-RULE-503-REMOTE
        when:
          all:
            - finding: FIND-SIP-CODE
              equals: "503"
            - finding: FIND-RESP-ORIGIN
              equals: remote
        supports: [HYP-PROVIDER-001]

      - id: EV-RULE-408
        when:
          finding: FIND-SIP-CODE
          equals: "408"
        supports: [HYP-NETWORK-001]
        strategy_hint: network-first

    confidence:
      gates:
        - id: CONF-GATE-ROOT
          name: root_cause_declare
          threshold: 85
          requires:
            - all_mandatory_evidence_collected
            - leading_hypothesis_has_supporting_evidence
            - no_active_contradicting_evidence
          blocks: RESOLUTION

      adjustments:
        - id: CONF-ADJ-LOCAL-404
          when:
            all:
              - finding: FIND-SIP-CODE
                equals: "404"
              - finding: FIND-RESP-ORIGIN
                equals: local
          boost_hypothesis: HYP-DP-001
          score_delta: 15

    decision:
      - id: DEC-RULE-ELIM-TRUNK
        type: elimination
        when:
          finding: FIND-REG-STATE
          in: [UP, REGISTERED]
        eliminates: HYP-TRUNK-001
        reason: SIP trunk registration is active
        alternatives:
          - alternative: SIP trunk down
            rejection_reason: show sip-ua status shows peers registered

      - id: DEC-RULE-ELIM-PROVIDER-LOCAL
        type: elimination
        when:
          all:
            - finding: FIND-SIP-CODE
              equals: "404"
            - finding: FIND-RESP-ORIGIN
              equals: local
        eliminates: HYP-PROVIDER-001
        reason: 404 generated locally, not by provider

    next_best_action:
      - id: NBA-001
        when:
          phase: COLLECTION
          evidence_missing: EVD-REQ-SIP-UA
        recommend:
          action_type: collect_evidence
          command_id: CMD-SIP-UA
        priority: 1

      - id: NBA-002
        when:
          phase: COLLECTION
          evidence_missing: EVD-REQ-SIP-DEBUG
          evidence_present: EVD-REQ-SIP-UA
        recommend:
          action_type: collect_evidence
          log_id: LOG-SIP-DEBUG
        priority: 2

      - id: NBA-003
        when:
          phase: INVESTIGATION
          hypothesis_active: HYP-DP-001
          evidence_missing: EVD-REQ-DIAL-PEER
        recommend:
          action_type: collect_evidence
          command_id: CMD-DIAL-PEER-RUN
        priority: 1

    questions:
      - id: Q-RULE-MOBILE
        when:
          phase: INVESTIGATION
          hypothesis_active: HYP-DP-001
        ask: Q-DISC-MOBILE
        priority: 1

  question_bank:
    - id: Q-DISC-MOBILE
      text: Are failing calls limited to mobile numbers, or also landline?
      category: discrimination
      target_field: affected_scope.destination_classes
      information_gain: 0.88
      discriminates: [HYP-DP-001, HYP-PROVIDER-001]

  cost_model:
    levels:
      low: { multiplier: 1, requires_approval: false }
      medium: { multiplier: 3, requires_approval: false }
      high: { multiplier: 8, requires_approval: true }
      critical: { multiplier: 25, requires_approval: true }
    action_types:
      ask_question: low
      show_command: low
      debug_log: medium
      config_change: critical
    selection:
      prefer_lower_cost: true
      minimum_information_gain: 0.3

  resolution:
    - id: RES-DIAL-PEER-FIX
      title: Correct dial-peer configuration
      description: Add or correct dial-peer covering failing destination prefix
      applies_to_hypothesis: HYP-DP-001
      requires_approval: true
      rollback_ref: RBK-DIAL-PEER

  verification:
    steps:
      - id: VER-LOCAL
        name: test_local_outbound
        description: Place outbound call to local landline
        expected: Call connects with two-way audio
        mandatory: true
      - id: VER-MOBILE
        name: test_mobile_outbound
        description: Place outbound call to mobile number
        expected: Call connects with two-way audio
        mandatory: true
      - id: VER-INTL
        name: test_international_outbound
        description: Place outbound call to international number
        expected: Call connects or documented out of scope
        mandatory: false
      - id: VER-INBOUND
        name: test_inbound_regression
        description: Confirm inbound PSTN calls still work
        expected: Inbound call connects
        mandatory: true
      - id: VER-NO-ERRORS
        name: confirm_no_new_errors
        description: Confirm no new CUBE errors in logging
        expected: No new SIP or dial-peer errors
        mandatory: true

  rollback:
    - id: RBK-DIAL-PEER
      applies_to: RES-DIAL-PEER-FIX
      description: Restore previous dial-peer configuration
      steps:
        - Restore dial-peer config from backup or change record
        - Verify with show dial-peer voice summary
      requires_approval: true

  preventive_actions:
    - id: PREV-CHECKLIST
      title: Dial-peer change checklist
      description: Validate all destination classes after any dial-peer modification
    - id: PREV-TEST-SCRIPT
      title: Post-change outbound test
      description: Test local, mobile, and international outbound after CUBE changes

  report:
    sections:
      - id: executive_summary
        title: Executive Summary
        required: true
      - id: root_cause_analysis
        title: Root Cause Analysis
        required: true
      - id: investigation_timeline
        title: Investigation Timeline
        required: true
      - id: evidence_appendix
        title: Evidence Appendix
        required: true
      - id: elimination_narrative
        title: Hypothesis Elimination
        required: true
      - id: preventive_actions
        title: Preventive Actions
        required: true

  learning:
    capture_fields:
      - symptoms
      - topology_pattern
      - evidence_signatures
      - root_cause_category
      - resolution_summary
      - lessons_learned
    anonymize:
      - hostname
      - ip_address
      - phone_number
      - customer_name
    lesson_templates:
      - After dial-peer edits, validate all destination classes including mobile
      - Local 404 on CUBE with registered trunk strongly indicates routing config gap
```

---

## 13. How DSL Maps to Canonical Data Model

| DSL Block | Canonical Object(s) |
|-----------|---------------------|
| `metadata` | Playbook |
| `platforms`, `topology` | Topology, Device (templates) |
| `symptoms`, `business_impact` | Case (intake defaults) |
| `intake.questions`, `question_bank` | Question |
| `evidence.requirements` | Evidence (requirements), Case.missing_evidence |
| `evidence.commands`, `evidence.logs` | InvestigationStep, Recommendation, LogArtifact, Configuration |
| `parsers.findings` | ParserFinding (extraction rules) |
| `hypotheses` | Hypothesis (seeds) |
| `rules.evidence` | ParserFinding → Hypothesis links, InvestigationGraph edges |
| `rules.confidence` | ConfidenceScore (gates, adjustments) |
| `rules.decision` | Decision (templates) |
| `rules.next_best_action` | Recommendation, InvestigationStep |
| `cost_model` | Recommendation.cost_level |
| `resolution` | Case.resolution, Recommendation |
| `verification.steps` | Verification |
| `rollback` | Recommendation.rollback_steps |
| `preventive_actions` | Case.preventive_action |
| `report.sections` | Report.sections |
| `learning` | LearningRecord |

---

## 14. How DSL Maps to Brain Engines

| Engine | DSL Consumption |
|--------|-----------------|
| Playbook Engine | Loads, validates, versions, and binds DSL playbooks to cases |
| Investigation Planner | Reads `strategies`, `rules.next_best_action`, proof objectives |
| Question Engine | Reads `intake.questions`, `rules.questions`, `question_bank` |
| Evidence Engine | Reads `evidence`, `parsers`, `rules.evidence` |
| Reasoning Engine | Reads `hypotheses`, `rules.evidence`, `rules.decision` |
| Confidence Engine | Reads `rules.confidence` |
| Decision Engine | Instantiates `rules.decision` into Decision objects |
| Cost Optimizer | Reads `cost_model`, command/log cost attributes |
| Topology Engine | Reads `topology` for pattern and completeness rules |
| State Machine | Reads phase requirements from evidence and verification blocks |
| Report Engine | Reads `report.sections` |
| Learning Engine | Reads `learning.capture_fields` and anonymization rules |
| Investigation Graph | Materializes edges from evidence and decision rules |
| Timeline Engine | Receives events when DSL-driven actions execute |

**Binding flow:**

```
.vpb.yaml → Playbook Engine (validate + parse)
         → Case.playbook_id + playbook_version
         → Engines evaluate rules against live canonical objects
```

---

## 15. Future Parser Design

The DSL parser (future implementation) will:

1. **Load** — Read `.vpb.yaml` from playbook repository
2. **Validate** — Schema validation against DSL JSON Schema (future artifact)
3. **Lint** — Anti-pattern checks (section 18)
4. **Compile** — Transform to internal Playbook object + rule index
5. **Bind** — Attach compiled playbook to Case at intake
6. **Evaluate** — Rule engine evaluates `when` conditions against ParserFinding, Hypothesis, and Evidence state
7. **Version** — Record `playbook.metadata.version` on Case for audit

Parser will **not** execute CLI commands or mutate devices. It produces canonical object templates and rule definitions only.

---

## 16. Versioning Strategy

| Element | Strategy |
|---------|----------|
| DSL `api_version` | Breaking schema changes increment (`voicepilot.io/v2`) |
| Playbook `metadata.version` | Semantic versioning (MAJOR.MINOR.PATCH) |
| MAJOR | Breaking rule semantics or required field changes |
| MINOR | New hypotheses, evidence, or optional rules |
| PATCH | Typo fixes, clarification, non-semantic edits |
| Case binding | Case records exact playbook ID + version at bind time |
| Deprecation | `metadata.status: deprecated` + `superseded_by` field (future) |
| Compatibility | Engines support current and previous `api_version` for 1 release |

---

## 17. Validation Rules

| Rule ID | Validation |
|---------|------------|
| VAL-001 | `metadata.id` matches `^VP-[A-Z]+-\d{4}$` |
| VAL-002 | All `requirement_id` references in commands/logs resolve |
| VAL-003 | All hypothesis IDs in rules exist in `hypotheses` |
| VAL-004 | All `eliminates` / `supports` / `contradicts` reference valid hypothesis IDs |
| VAL-005 | At least one `confidence.gates` entry blocks RESOLUTION |
| VAL-006 | Mandatory verification steps have `expected` defined |
| VAL-007 | `config_change` or `service_restart` actions have `rollback_ref` |
| VAL-008 | No duplicate IDs within same playbook scope |
| VAL-009 | `question_bank` IDs referenced in `rules.questions` exist |
| VAL-010 | `cost` values are valid levels: low, medium, high, critical |
| VAL-011 | Deprecated playbooks cannot have `status: active` without review flag |
| VAL-012 | `learning.anonymize` must include hostname, ip_address, phone_number |

---

## 18. Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|--------------|--------------|------------------|
| Prose-only investigation steps | Engines cannot evaluate | Use structured `commands`, `rules`, `hypotheses` |
| Root cause in playbook text | Violates evidence-first principle | Define hypotheses and confirmation gates only |
| Missing mandatory evidence | Premature conclusion risk | Set `blocks_confirmation: true` on required evidence |
| No alternatives in decision rules | Audit failure | Include `alternatives` with `rejection_reason` |
| Critical action without rollback | Engineer trust failure | Always pair `config_change` with `rollback` |
| Duplicate hypothesis IDs | Rule evaluation ambiguity | Unique IDs across playbook |
| Catch-all evidence rule | False positive eliminations | Specific `when` conditions with signal types |
| Chat-style questions | Unparseable answers | `target_field` on every question |
| Hardcoded device hostnames | Not reusable | Use `device_role` not hostname |
| Skipping verification | Unverified resolution | Mandatory verification steps per playbook |
| Confidence gate without threshold | Unmeasurable confirmation | Always set numeric `threshold` |
| Learning without anonymize | PII leakage risk | Always declare `learning.anonymize` fields |

---

*VoicePilot DSL Specification v1.0.0-draft — Sprint 0, Day 4*  
*Review status: Draft for Distinguished Engineer review*
