# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-ccd7c30cd19a
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-21T00:03:29.041981+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-f9d903731bfe
- **Confidence:** 98%

## Evidence Findings

- `show dial-peer voice summary`: **dial_peer_summary_present** (parser:cisco_show_dial_peer_voice_summary) — Dial-peer voice summary output detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **dial_peer_config_present** (parser:cisco_show_dial_peer_voice_summary) — Dial-peer configuration entries detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **outbound_dial_peer_candidates_present** (parser:cisco_show_dial_peer_voice_summary) — Outbound VoIP dial-peer candidates with destination patterns detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **session_target_present** (parser:cisco_show_dial_peer_voice_summary) — Session target configuration detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show sip-ua status`: **sip_ua_disabled** (parser:cisco_show_sip_ua_status) — SIP user agent is disabled — structured: sip_ua_enabled=False, registration_state=unknown
- `show run | sec voice service voip`: **voice_service_voip_present** (parser:cisco_show_run_voice_service_voip) — voice service voip configuration present — structured: sip_ua_disabled_by_config=True
- `show run | sec voice service voip`: **sip_ua_disabled_by_config** (parser:cisco_show_run_voice_service_voip) — SIP user agent disabled by configuration — structured: sip_ua_disabled_by_config=True
- `debug ccsip messages`: **sip_trace_present** (parser:cisco_debug_ccsip_messages) — SIP message trace markers detected — structured: response_codes=[503]
- `debug ccsip messages`: **sip_503_detected** (parser:cisco_debug_ccsip_messages) — SIP response 503 Service Unavailable — structured: response_codes=[503]
- `debug ccsip messages`: **sip_call_id_present** (parser:cisco_debug_ccsip_messages) — Call-ID header detected in SIP trace — structured: response_codes=[503]
- `debug ccsip messages`: **sip_invite_present** (parser:cisco_debug_ccsip_messages) — INVITE method detected in SIP trace — structured: response_codes=[503]

## Canonical Voice Objects

- DialPeer 1 — destination 9T — cisco_show_dial_peer_voice_summary — show dial-peer voice summary — 100%
- DialPeer 2 — destination 8011 — cisco_show_dial_peer_voice_summary — show dial-peer voice summary — 100%
- SipUA — SIP-UA — cisco_show_sip_ua_status — show sip-ua status — 70%
- VoiceService — voice service voip — cisco_show_run_voice_service_voip — show run | sec voice service voip — 70%

## Call Path Analysis

### DialPeer 1 → Provider-192.0.2.10
- **Direction:** outbound
- **Source:** DialPeer 1
- **Destination:** Provider-192.0.2.10

**Hops:**
1. DialPeer 1
2. Provider-192.0.2.10

**Warnings:**
_None_

**Breakpoints:**
_None on path._

### DialPeer 2 → Provider-198.51.100.20
- **Direction:** outbound
- **Source:** DialPeer 2
- **Destination:** Provider-198.51.100.20

**Hops:**
1. DialPeer 2
2. Provider-198.51.100.20

**Warnings:**
_None_

**Breakpoints:**
_None on path._

**Note:** SIP-UA is disabled and may affect all SIP call processing, even if not directly present in the current path graph.

## Health Assessment

- **Overall Score:** 60/100
- **Status:** FAIL
- **Counts:** PASS 4 | WARN 1 | FAIL 1 | UNKNOWN 0
- **Severity Counts:** critical 1, medium 1
- **Category Counts:** configuration 1, sip 1

**Findings:**
- CRITICAL FAIL — SIP-UA is disabled.
  Recommendation: Enable SIP-UA and validate registration.
- MEDIUM WARN — allow-connections policy is missing from voice service configuration.
  Recommendation: Review voice service voip allow-connections settings.

**Recommendations:**
- Enable SIP-UA and validate registration.
- Review voice service voip allow-connections settings.

## Matched Knowledge

### CISCO-BP-SIP-UA-ENABLED
- **Knowledge ID:** CISCO-BP-SIP-UA-ENABLED
- **Title:** SIP-UA must be enabled for CUBE SIP processing
- **Severity:** CRITICAL
- **Category:** BEST_PRACTICE
- **Matched object:** SipUA
- **Recommendation:** Enable SIP-UA and verify SIP registration before closing the incident.
- **References:** Cisco CUBE SIP service best practice

### CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS
- **Knowledge ID:** CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS
- **Title:** Voice service allow-connections policy should be configured
- **Severity:** MEDIUM
- **Category:** BEST_PRACTICE
- **Matched object:** VoiceService
- **Recommendation:** Verify allow-connections sip to sip is configured where CUBE is expected to interwork SIP legs.
- **References:** Cisco CUBE basic SIP-SIP interworking guidance

## Correlation Reasoning

- **sip_ua_disabled_confirmed** — reinforcement, +8 confidence
  Operational status and running configuration both indicate SIP-UA is disabled.
  Evidence: sip_ua_disabled, sip_ua_disabled_by_config

## Decision Timeline

00:03:29
discovery_planned
Discovery plan generated
Discovery plan generated with 4 recommendation(s). Next best command: show dial-peer voice summary.
Confidence: 0 → 65

↓

00:03:29
Evidence
Evidence collected: show dial-peer voice summary
CLI evidence submitted for command `show dial-peer voice summary`.

↓

00:03:29
Evidence
Evidence collected: show sip-ua status
CLI evidence submitted for command `show sip-ua status`.

↓

00:03:29
Evidence
Evidence collected: show run | sec voice service voip
CLI evidence submitted for command `show run | sec voice service voip`.

↓

00:03:29
Evidence
Evidence collected: debug ccsip messages
CLI evidence submitted for command `debug ccsip messages`.

↓

00:03:29
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_summary_present
Evidence: dial_peer_summary_present

↓

00:03:29
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_config_present
Evidence: dial_peer_config_present

↓

00:03:29
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected outbound_dial_peer_candidates_present
Evidence: outbound_dial_peer_candidates_present

↓

00:03:29
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected session_target_present
Evidence: session_target_present

↓

00:03:29
Parser
CiscoShowSipUaStatusParser
Detected sip_ua_disabled
Evidence: sip_ua_disabled

↓

00:03:29
Parser
CiscoShowRunVoiceServiceVoipParser
Detected voice_service_voip_present
Evidence: voice_service_voip_present

↓

00:03:29
Parser
CiscoShowRunVoiceServiceVoipParser
Detected sip_ua_disabled_by_config
Evidence: sip_ua_disabled_by_config

↓

00:03:29
Parser
CiscoDebugCcsipMessagesParser
Detected sip_trace_present
Evidence: sip_trace_present

↓

00:03:29
Parser
CiscoDebugCcsipMessagesParser
Detected sip_503_detected
Evidence: sip_503_detected

↓

00:03:29
Parser
CiscoDebugCcsipMessagesParser
Detected sip_call_id_present
Evidence: sip_call_id_present

↓

00:03:29
Parser
CiscoDebugCcsipMessagesParser
Detected sip_invite_present
Evidence: sip_invite_present

↓

00:03:29
Hypothesis
CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-7520815c69dd

↓

00:03:29
Hypothesis
Provider or SIP trunk service issue
SIP 503 with trace present points to provider or trunk service rejection.
Evidence: FIND-416369d42bc7, FIND-d9f602c04642

↓

00:03:29
Correlation — Rule fired
sip_ua_disabled_confirmed
Operational status and running configuration both indicate SIP-UA is disabled.
Confidence: 90 → 98
Evidence: sip_ua_disabled, sip_ua_disabled_by_config

↓

00:03:29
Confidence
CUBE SIP user agent disabled
Confidence changed from 90% to 98% (reinforcement).
Confidence: 90 → 98

↓

00:03:29
Recommendation
Likely Root Cause — CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-7520815c69dd
Rejected: Provider or SIP trunk service issue

↓

00:03:29
Verification
VER-001
show sip-ua status reports SIP-UA enabled — passed

↓

00:03:29
Verification
VER-002
Provider trunk shows registered/UP — passed

↓

00:03:29
Verification
VER-003
Place controlled outbound test call — passed

↓

00:03:29
Learning
Learning record created
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled
Evidence: FIND-1897aba7433a, FIND-6a5a5d9c55a9, FIND-d3fb6c56c781, FIND-1cf92c383c04, FIND-7520815c69dd, FIND-843fc384200a, FIND-7bd8cea224d0, FIND-416369d42bc7, FIND-d9f602c04642, FIND-b83db98bc2bb, FIND-d377e7157874

↓

00:03:29
Case Closed
Case closed
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled

## Recommendation

Likely root cause identified: CUBE SIP user agent disabled Likely root cause: CUBE SIP user agent disabled SIP user agent is disabled on CUBE, blocking outbound SIP processing.

**Recommended Actions:**
- Review voice service voip configuration on CUBE
- Enable SIP user agent if currently disabled

## Discovery Plan

- **Current Confidence:** 98%
- **Estimated Final Confidence:** 98%
- **Remaining Uncertainty:** 2%

**Recommended Evidence:**
_No additional evidence recommended._

## Investigation Quality

- **Overall Score:** 100/100
- **Overall Status:** PASS
- **Ready for Recommendation:** Yes
- **Ready for Case Closure:** Yes

### Evidence Completeness

- **Score:** 100/100
- **Status:** PASS
- **Summary:** All required and optional discovery evidence has been collected.

**Recommendations:**
- _None_


## Investigation Journey

- **Session ID:** SES-8d781ab0a1af
- **Steps:** 25

**Journey:**
1. `intake_question` (INTAKE) — Investigation session started
2. `intake_question` (INTAKE) — Presented intake question
3. `intake_question` (INTAKE) — Answered Q-INT-001
4. `intake_question` (INTAKE) — Answered Q-INT-002
5. `intake_question` (INTAKE) — Answered Q-INT-003
6. `intake_question` (INTAKE) — Answered Q-INT-004
7. `discovery_planning` (DISCOVERY) — Intake completed
8. `collect_evidence` (COLLECTION) — Discovery planning complete; evidence collection started
9. `collect_evidence` (COLLECTION) — Collected evidence for `show dial-peer voice summary`
10. `collect_evidence` (COLLECTION) — Collected evidence for `show sip-ua status`
11. `collect_evidence` (COLLECTION) — Collected evidence for `show run | sec voice service voip`
12. `run_analysis` (ANALYSIS) — Collected evidence for `debug ccsip messages`
13. `run_hypothesis` (HYPOTHESIS) — Analysis complete
14. `run_correlation` (INVESTIGATION) — Hypothesis generation complete
15. `quality_evaluation` (INVESTIGATION) — Correlation complete
16. `run_recommendation` (INVESTIGATION) — Quality score 100/100 — ready for recommendation
17. `run_verification` (RESOLUTION) — Recommendation generated; verification required
18. `run_verification` (RESOLUTION) — Verification checklist generated
19. `run_verification` (RESOLUTION) — Verification status recorded for step 1
20. `run_verification` (RESOLUTION) — Verification notes recorded for step 1
21. `run_verification` (RESOLUTION) — Verification status recorded for step 2
22. `run_verification` (RESOLUTION) — Verification notes recorded for step 2
23. `run_verification` (RESOLUTION) — Verification status recorded for step 3
24. `run_closure` (LEARNING) — Verification complete
25. `run_closure` (CLOSED) — Case closed with learning record


## Verification

- **Outcome:** all steps passed
- VER-001: show sip-ua status reports SIP-UA enabled — **passed** (SIP-UA enabled after change)
- VER-002: Provider trunk shows registered/UP — **passed** (Provider trunk registered)
- VER-003: Place controlled outbound test call — **passed** (Outbound test call successful)

## Learning Record

- **Learning Record ID:** LRN-88b04f4fce10
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-21T00:03:29.039924+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-21T00:03:29.039960+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-21T00:03:29.039989+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-21T00:03:29.040016+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-21T00:03:29.040044+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-21T00:03:29.040287+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-21T00:03:29.040350+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-21T00:03:29.040405+00:00] evidence_collected: Collected CLI evidence for: show run | sec voice service voip
9. [2026-06-21T00:03:29.040460+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
