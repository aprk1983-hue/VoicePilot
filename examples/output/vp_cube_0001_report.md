# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-7d5e5385a728
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-19T16:05:50.676045+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-69faa3b773fc
- **Confidence:** 90%

## Evidence Findings

- `show dial-peer voice summary`: **dial_peer_summary_present** (parser:cisco_show_dial_peer_voice_summary) — Dial-peer voice summary output detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **dial_peer_config_present** (parser:cisco_show_dial_peer_voice_summary) — Dial-peer configuration entries detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **outbound_dial_peer_candidates_present** (parser:cisco_show_dial_peer_voice_summary) — Outbound VoIP dial-peer candidates with destination patterns detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show dial-peer voice summary`: **session_target_present** (parser:cisco_show_dial_peer_voice_summary) — Session target configuration detected — structured: dial_peer_count=2, voip_dial_peer_count=2
- `show sip-ua status`: **sip_ua_disabled** (parser:cisco_show_sip_ua_status) — SIP user agent is disabled — structured: sip_ua_enabled=False, registration_state=unknown
- `debug ccsip messages`: **sip_trace_present** (parser:cisco_debug_ccsip_messages) — SIP message trace markers detected — structured: response_codes=[503]
- `debug ccsip messages`: **sip_503_detected** (parser:cisco_debug_ccsip_messages) — SIP response 503 Service Unavailable — structured: response_codes=[503]
- `debug ccsip messages`: **sip_call_id_present** (parser:cisco_debug_ccsip_messages) — Call-ID header detected in SIP trace — structured: response_codes=[503]
- `debug ccsip messages`: **sip_invite_present** (parser:cisco_debug_ccsip_messages) — INVITE method detected in SIP trace — structured: response_codes=[503]

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

- **Learning Record ID:** LRN-b8c8e90a9076
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-19T16:05:50.675315+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-19T16:05:50.675331+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-19T16:05:50.675342+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-19T16:05:50.675353+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-19T16:05:50.675364+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-19T16:05:50.675440+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-19T16:05:50.675459+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-19T16:05:50.675475+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
