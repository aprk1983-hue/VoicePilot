# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-5c633bf7d57b
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-19T15:46:51.399832+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-b39e47d5d68f
- **Confidence:** 90%

## Evidence Findings

- `show dial-peer voice summary`: **dial_peer_summary_present** — Dial-peer voice summary output detected
- `show dial-peer voice summary`: **dial_peer_config_present** — Dial-peer configuration entries detected
- `show dial-peer voice summary`: **outbound_dial_peer_candidates_present** — Outbound VoIP dial-peer candidates with destination patterns detected
- `show dial-peer voice summary`: **session_target_present** — Session target configuration detected
- `show sip-ua status`: **sip_ua_disabled** — SIP user agent is disabled
- `debug ccsip messages`: **sip_trace_present** — SIP message trace markers detected
- `debug ccsip messages`: **sip_503_detected** — SIP response 503 Service Unavailable

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

- **Learning Record ID:** LRN-340266788dd0
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-19T15:46:51.399301+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-19T15:46:51.399316+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-19T15:46:51.399327+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-19T15:46:51.399337+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-19T15:46:51.399347+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-19T15:46:51.399416+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-19T15:46:51.399432+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-19T15:46:51.399448+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
