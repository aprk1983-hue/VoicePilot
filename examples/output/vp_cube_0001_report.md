# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-afd045b137e9
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-19T15:38:32.039207+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-8710e32d2dca
- **Confidence:** 90%

## Evidence Findings

- `show dial-peer voice summary`: **dial_peer_config_present**
- `show sip-ua status`: **sip_ua_disabled** — SIP user agent is disabled
- `debug ccsip messages`: **sip_503_detected**

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

- **Learning Record ID:** LRN-db6472349174
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-19T15:38:32.038692+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-19T15:38:32.038709+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-19T15:38:32.038720+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-19T15:38:32.038730+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-19T15:38:32.038741+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-19T15:38:32.038818+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-19T15:38:32.038835+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-19T15:38:32.038851+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
