# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-9786623b7939
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-20T05:21:51.612071+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-4027c0a86cd5
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
- Review voice service voip allow-connections settings.
- Enable SIP-UA and validate registration.

## Matched Knowledge

### CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS
- **Knowledge ID:** CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS
- **Title:** Voice service allow-connections policy should be configured
- **Severity:** MEDIUM
- **Category:** BEST_PRACTICE
- **Matched object:** VoiceService
- **Recommendation:** Verify allow-connections sip to sip is configured where CUBE is expected to interwork SIP legs.
- **References:** Cisco CUBE basic SIP-SIP interworking guidance

### CISCO-BP-SIP-UA-ENABLED
- **Knowledge ID:** CISCO-BP-SIP-UA-ENABLED
- **Title:** SIP-UA must be enabled for CUBE SIP processing
- **Severity:** CRITICAL
- **Category:** BEST_PRACTICE
- **Matched object:** SipUA
- **Recommendation:** Enable SIP-UA and verify SIP registration before closing the incident.
- **References:** Cisco CUBE SIP service best practice

## Correlation Reasoning

- **sip_ua_disabled_confirmed** — reinforcement, +8 confidence
  Operational status and running configuration both indicate SIP-UA is disabled.
  Evidence: sip_ua_disabled, sip_ua_disabled_by_config

## Decision Timeline

05:21:51
Evidence
Evidence collected: show dial-peer voice summary
CLI evidence submitted for command `show dial-peer voice summary`.

↓

05:21:51
Evidence
Evidence collected: show sip-ua status
CLI evidence submitted for command `show sip-ua status`.

↓

05:21:51
Evidence
Evidence collected: show run | sec voice service voip
CLI evidence submitted for command `show run | sec voice service voip`.

↓

05:21:51
Evidence
Evidence collected: debug ccsip messages
CLI evidence submitted for command `debug ccsip messages`.

↓

05:21:51
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_summary_present
Evidence: dial_peer_summary_present

↓

05:21:51
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_config_present
Evidence: dial_peer_config_present

↓

05:21:51
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected outbound_dial_peer_candidates_present
Evidence: outbound_dial_peer_candidates_present

↓

05:21:51
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected session_target_present
Evidence: session_target_present

↓

05:21:51
Parser
CiscoShowSipUaStatusParser
Detected sip_ua_disabled
Evidence: sip_ua_disabled

↓

05:21:51
Parser
CiscoShowRunVoiceServiceVoipParser
Detected voice_service_voip_present
Evidence: voice_service_voip_present

↓

05:21:51
Parser
CiscoShowRunVoiceServiceVoipParser
Detected sip_ua_disabled_by_config
Evidence: sip_ua_disabled_by_config

↓

05:21:51
Parser
CiscoDebugCcsipMessagesParser
Detected sip_trace_present
Evidence: sip_trace_present

↓

05:21:51
Parser
CiscoDebugCcsipMessagesParser
Detected sip_503_detected
Evidence: sip_503_detected

↓

05:21:51
Parser
CiscoDebugCcsipMessagesParser
Detected sip_call_id_present
Evidence: sip_call_id_present

↓

05:21:51
Parser
CiscoDebugCcsipMessagesParser
Detected sip_invite_present
Evidence: sip_invite_present

↓

05:21:51
Hypothesis
CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-bb6e35628164

↓

05:21:51
Hypothesis
Provider or SIP trunk service issue
SIP 503 with trace present points to provider or trunk service rejection.
Evidence: FIND-6988a823828e, FIND-c5be1dc13a74

↓

05:21:51
Correlation — Rule fired
sip_ua_disabled_confirmed
Operational status and running configuration both indicate SIP-UA is disabled.
Confidence: 90 → 98
Evidence: sip_ua_disabled, sip_ua_disabled_by_config

↓

05:21:51
Confidence
CUBE SIP user agent disabled
Confidence changed from 90% to 98% (reinforcement).
Confidence: 90 → 98

↓

05:21:51
Recommendation
Likely Root Cause — CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-bb6e35628164
Rejected: Provider or SIP trunk service issue

↓

05:21:51
Verification
VER-001
show sip-ua status reports SIP-UA enabled — passed

↓

05:21:51
Verification
VER-002
Provider trunk shows registered/UP — passed

↓

05:21:51
Verification
VER-003
Place controlled outbound test call — passed

↓

05:21:51
Learning
Learning record created
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled
Evidence: FIND-2c77dc1f280f, FIND-6b8bf54eccd7, FIND-6f48389bb622, FIND-553f0d052a06, FIND-bb6e35628164, FIND-d0f86c7760b7, FIND-6d9b382c2dbb, FIND-c5be1dc13a74, FIND-6988a823828e, FIND-976b7bf16d89, FIND-463f9700372d

↓

05:21:51
Case Closed
Case closed
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled

## Recommendation

Likely root cause identified: CUBE SIP user agent disabled Likely root cause: CUBE SIP user agent disabled SIP user agent is disabled on CUBE, blocking outbound SIP processing.

**Recommended Actions:**
- Review voice service voip configuration on CUBE
- Enable SIP user agent if currently disabled

## Verification

- **Outcome:** all steps passed
- VER-001: show sip-ua status reports SIP-UA enabled — **passed** (SIP-UA enabled after change)
- VER-002: Provider trunk shows registered/UP — **passed** (Provider trunk registered)
- VER-003: Place controlled outbound test call — **passed** (Outbound test call successful)

## Learning Record

- **Learning Record ID:** LRN-a5f4b47cd3d6
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-20T05:21:51.610955+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-20T05:21:51.610973+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-20T05:21:51.610986+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-20T05:21:51.610996+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-20T05:21:51.611008+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-20T05:21:51.611125+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-20T05:21:51.611163+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-20T05:21:51.611193+00:00] evidence_collected: Collected CLI evidence for: show run | sec voice service voip
9. [2026-06-20T05:21:51.611221+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
