# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-034cef347eae
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-20T02:40:20.062895+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-aad128bfe490
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

## Correlation Reasoning

- **sip_ua_disabled_confirmed** — reinforcement, +8 confidence
  Operational status and running configuration both indicate SIP-UA is disabled.
  Evidence: sip_ua_disabled, sip_ua_disabled_by_config

## Decision Timeline

02:40:20
Evidence
Evidence collected: show dial-peer voice summary
CLI evidence submitted for command `show dial-peer voice summary`.

↓

02:40:20
Evidence
Evidence collected: show sip-ua status
CLI evidence submitted for command `show sip-ua status`.

↓

02:40:20
Evidence
Evidence collected: show run | sec voice service voip
CLI evidence submitted for command `show run | sec voice service voip`.

↓

02:40:20
Evidence
Evidence collected: debug ccsip messages
CLI evidence submitted for command `debug ccsip messages`.

↓

02:40:20
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_summary_present
Evidence: dial_peer_summary_present

↓

02:40:20
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_config_present
Evidence: dial_peer_config_present

↓

02:40:20
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected outbound_dial_peer_candidates_present
Evidence: outbound_dial_peer_candidates_present

↓

02:40:20
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected session_target_present
Evidence: session_target_present

↓

02:40:20
Parser
CiscoShowSipUaStatusParser
Detected sip_ua_disabled
Evidence: sip_ua_disabled

↓

02:40:20
Parser
CiscoShowRunVoiceServiceVoipParser
Detected voice_service_voip_present
Evidence: voice_service_voip_present

↓

02:40:20
Parser
CiscoShowRunVoiceServiceVoipParser
Detected sip_ua_disabled_by_config
Evidence: sip_ua_disabled_by_config

↓

02:40:20
Parser
CiscoDebugCcsipMessagesParser
Detected sip_trace_present
Evidence: sip_trace_present

↓

02:40:20
Parser
CiscoDebugCcsipMessagesParser
Detected sip_503_detected
Evidence: sip_503_detected

↓

02:40:20
Parser
CiscoDebugCcsipMessagesParser
Detected sip_call_id_present
Evidence: sip_call_id_present

↓

02:40:20
Parser
CiscoDebugCcsipMessagesParser
Detected sip_invite_present
Evidence: sip_invite_present

↓

02:40:20
Hypothesis
CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-6e2345024463

↓

02:40:20
Hypothesis
Provider or SIP trunk service issue
SIP 503 with trace present points to provider or trunk service rejection.
Evidence: FIND-40cc52496fc5, FIND-7281b239a8c7

↓

02:40:20
Correlation — Rule fired
sip_ua_disabled_confirmed
Operational status and running configuration both indicate SIP-UA is disabled.
Confidence: 90 → 98
Evidence: sip_ua_disabled, sip_ua_disabled_by_config

↓

02:40:20
Confidence
CUBE SIP user agent disabled
Confidence changed from 90% to 98% (reinforcement).
Confidence: 90 → 98

↓

02:40:20
Recommendation
Likely Root Cause — CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-6e2345024463
Rejected: Provider or SIP trunk service issue

↓

02:40:20
Verification
VER-001
show sip-ua status reports SIP-UA enabled — passed

↓

02:40:20
Verification
VER-002
Provider trunk shows registered/UP — passed

↓

02:40:20
Verification
VER-003
Place controlled outbound test call — passed

↓

02:40:20
Learning
Learning record created
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled
Evidence: FIND-053d61d9b2b7, FIND-d6af4c30bade, FIND-dfeda2a96c94, FIND-2e7126f0060f, FIND-6e2345024463, FIND-ff7122afe4cd, FIND-7beb573e26ca, FIND-40cc52496fc5, FIND-7281b239a8c7, FIND-a681cd3358e8, FIND-8e9cc7f34b82

↓

02:40:20
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

- **Learning Record ID:** LRN-c70115b025f7
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-20T02:40:20.061766+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-20T02:40:20.061783+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-20T02:40:20.061796+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-20T02:40:20.061806+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-20T02:40:20.061816+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-20T02:40:20.061926+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-20T02:40:20.061962+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-20T02:40:20.061993+00:00] evidence_collected: Collected CLI evidence for: show run | sec voice service voip
9. [2026-06-20T02:40:20.062023+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
