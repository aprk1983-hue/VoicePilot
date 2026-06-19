# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-710d41d2ca20
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-19T18:00:50.966455+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-372bb5d0c38d
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

## Correlation Reasoning

- **sip_ua_disabled_confirmed** — reinforcement, +8 confidence
  Operational status and running configuration both indicate SIP-UA is disabled.
  Evidence: sip_ua_disabled, sip_ua_disabled_by_config

## Decision Timeline

18:00:50
Evidence
Evidence collected: show dial-peer voice summary
CLI evidence submitted for command `show dial-peer voice summary`.

↓

18:00:50
Evidence
Evidence collected: show sip-ua status
CLI evidence submitted for command `show sip-ua status`.

↓

18:00:50
Evidence
Evidence collected: show run | sec voice service voip
CLI evidence submitted for command `show run | sec voice service voip`.

↓

18:00:50
Evidence
Evidence collected: debug ccsip messages
CLI evidence submitted for command `debug ccsip messages`.

↓

18:00:50
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_summary_present
Evidence: dial_peer_summary_present

↓

18:00:50
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected dial_peer_config_present
Evidence: dial_peer_config_present

↓

18:00:50
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected outbound_dial_peer_candidates_present
Evidence: outbound_dial_peer_candidates_present

↓

18:00:50
Parser
CiscoShowDialPeerVoiceSummaryParser
Detected session_target_present
Evidence: session_target_present

↓

18:00:50
Parser
CiscoShowSipUaStatusParser
Detected sip_ua_disabled
Evidence: sip_ua_disabled

↓

18:00:50
Parser
CiscoShowRunVoiceServiceVoipParser
Detected voice_service_voip_present
Evidence: voice_service_voip_present

↓

18:00:50
Parser
CiscoShowRunVoiceServiceVoipParser
Detected sip_ua_disabled_by_config
Evidence: sip_ua_disabled_by_config

↓

18:00:50
Parser
CiscoDebugCcsipMessagesParser
Detected sip_trace_present
Evidence: sip_trace_present

↓

18:00:50
Parser
CiscoDebugCcsipMessagesParser
Detected sip_503_detected
Evidence: sip_503_detected

↓

18:00:50
Parser
CiscoDebugCcsipMessagesParser
Detected sip_call_id_present
Evidence: sip_call_id_present

↓

18:00:50
Parser
CiscoDebugCcsipMessagesParser
Detected sip_invite_present
Evidence: sip_invite_present

↓

18:00:50
Hypothesis
CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-d78079941369

↓

18:00:50
Hypothesis
Provider or SIP trunk service issue
SIP 503 with trace present points to provider or trunk service rejection.
Evidence: FIND-ccb41b3129af, FIND-4107c0329ab4

↓

18:00:50
Correlation — Rule fired
sip_ua_disabled_confirmed
Operational status and running configuration both indicate SIP-UA is disabled.
Confidence: 90 → 98
Evidence: sip_ua_disabled, sip_ua_disabled_by_config

↓

18:00:50
Confidence
CUBE SIP user agent disabled
Confidence changed from 90% to 98% (reinforcement).
Confidence: 90 → 98

↓

18:00:50
Recommendation
Likely Root Cause — CUBE SIP user agent disabled
SIP user agent is disabled on CUBE, blocking outbound SIP processing.
Evidence: FIND-d78079941369
Rejected: Provider or SIP trunk service issue

↓

18:00:50
Verification
VER-001
show sip-ua status reports SIP-UA enabled — passed

↓

18:00:50
Verification
VER-002
Provider trunk shows registered/UP — passed

↓

18:00:50
Verification
VER-003
Place controlled outbound test call — passed

↓

18:00:50
Learning
Learning record created
Review voice service voip configuration on CUBE; Enable SIP user agent if currently disabled
Evidence: FIND-5f13b01a7435, FIND-7c1a6c35900a, FIND-03c228f1ed6b, FIND-981923b301f8, FIND-d78079941369, FIND-65e97b7abe22, FIND-ed2054401cb8, FIND-4107c0329ab4, FIND-ccb41b3129af, FIND-5031fbd7b876, FIND-4565340798c1

↓

18:00:50
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

- **Learning Record ID:** LRN-a783b9e0ee94
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-19T18:00:50.965436+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-19T18:00:50.965453+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-19T18:00:50.965465+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-19T18:00:50.965475+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-19T18:00:50.965486+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-19T18:00:50.965592+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-19T18:00:50.965628+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-19T18:00:50.965657+00:00] evidence_collected: Collected CLI evidence for: show run | sec voice service voip
9. [2026-06-19T18:00:50.965685+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
