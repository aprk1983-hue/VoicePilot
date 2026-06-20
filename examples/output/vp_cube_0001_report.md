# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-dfd714d3cfe1
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-20T04:31:59.513783+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-e171c474ca59
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

04:31:59
Evidence
Evidence collected: show dial-peer voice summary
CLI evidence submitted for command `show dial-peer voice summary`.

↓

04:31:59
Evidence
Evidence collected: show sip-ua status
CLI evidence submitted for command `show sip-ua status`.

↓

04:31:59
Evidence
Evidence collected: show run | sec voice service voip
CLI evidence submitted for command `show run | sec voice service voip`.

↓

04:31:59
Evidence
Evidence collected: debug ccsip messages
CLI evidence submitted for command `debug ccsip messages`.

↓

04:31:59
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_summary_present
Evidence: dial_peer_summary_present

↓

04:31:59
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_config_present
Evidence: dial_peer_config_present

↓

04:31:59
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected outbound_dial_peer_candidates_present
Evidence: outbound_dial_peer_candidates_present

↓

04:31:59
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected session_target_present
Evidence: session_target_present

↓

04:31:59
Parser
CiscoShowSipUaStatusParser
Detected sip_ua_disabled
Evidence: sip_ua_disabled

↓

04:31:59
Parser
CiscoShowRunVoiceServiceVoipParser
Detected voice_service_voip_present
Evidence: voice_service_voip_present

↓

04:31:59
Parser
CiscoShowRunVoiceServiceVoipParser
Detected sip_ua_disabled_by_config
Evidence: sip_ua_disabled_by_config

↓

04:31:59
Parser
CiscoDebugCcsipMessagesParser
Detected sip_trace_present
Evidence: sip_trace_present

↓

04:31:59
Parser
CiscoDebugCcsipMessagesParser
Detected sip_503_detected
Evidence: sip_503_detected

↓

04:31:59
Parser
CiscoDebugCcsipMessagesParser
Detected sip_call_id_present
Evidence: sip_call_id_present

↓

04:31:59
Parser
CiscoDebugCcsipMessagesParser
Detected sip_invite_present
Evidence: sip_invite_present

↓

04:31:59
Hypothesis
CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-ec27cb53e9e2

↓

04:31:59
Hypothesis
Provider or SIP trunk service issue
SIP 503 with trace present points to provider or trunk service rejection.
Evidence: FIND-f8a8de06ab34, FIND-bfdd4b8532bc

↓

04:31:59
Correlation — Rule fired
sip_ua_disabled_confirmed
Operational status and running configuration both indicate SIP-UA is disabled.
Confidence: 90 → 98
Evidence: sip_ua_disabled, sip_ua_disabled_by_config

↓

04:31:59
Confidence
CUBE SIP user agent disabled
Confidence changed from 90% to 98% (reinforcement).
Confidence: 90 → 98

↓

04:31:59
Recommendation
Likely Root Cause — CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-ec27cb53e9e2
Rejected: Provider or SIP trunk service issue

↓

04:31:59
Verification
VER-001
show sip-ua status reports SIP-UA enabled — passed

↓

04:31:59
Verification
VER-002
Provider trunk shows registered/UP — passed

↓

04:31:59
Verification
VER-003
Place controlled outbound test call — passed

↓

04:31:59
Learning
Learning record created
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled
Evidence: FIND-001692801aea, FIND-850394f1f5a6, FIND-1d53c4adee6b, FIND-81b7174f4e52, FIND-ec27cb53e9e2, FIND-281f8c30a6be, FIND-3bfc82699ccf, FIND-bfdd4b8532bc, FIND-f8a8de06ab34, FIND-f4786a616746, FIND-3153ab70b443

↓

04:31:59
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

- **Learning Record ID:** LRN-28358c147b89
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-20T04:31:59.512621+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-20T04:31:59.512639+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-20T04:31:59.512651+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-20T04:31:59.512661+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-20T04:31:59.512671+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-20T04:31:59.512783+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-20T04:31:59.512822+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-20T04:31:59.512853+00:00] evidence_collected: Collected CLI evidence for: show run | sec voice service voip
9. [2026-06-20T04:31:59.512882+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
