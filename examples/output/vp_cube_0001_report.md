# VoicePilot Incident Report

## Case Overview

- **Case ID:** CASE-58453ebdf8c4
- **Playbook ID:** VP-CUBE-0001
- **Final State:** CLOSED
- **Closed At:** 2026-06-19T15:29:01.392406+00:00

## Symptom

outbound, PSTN, external, off-net

## Root Cause Assessment

- **Top Hypothesis:** CUBE SIP user agent disabled
- **Hypothesis ID:** HYP-d48621ab6423
- **Confidence:** 90%

## Evidence Findings

- `show dial-peer voice summary`: **dial_peer_config_present**
- `show sip-ua status`: **sip_ua_disabled**
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

- **Learning Record ID:** LRN-d25dc8545be8
- **Root Cause:** CUBE SIP user agent disabled
- **Reusable Pattern:** VP-CUBE-0001:HYP-SIP-UA-DISABLED
- **Lessons Learned:** Playbook VP-CUBE-0001 investigation verified 'CUBE SIP user agent disabled'. Always collect correlated CLI evidence and verification before closure. Next focus: Review voice service voip configuration on CUBE.

## Timeline

0. [intake] symptom_onset: Symptom onset recorded: 2026-06-10
1. [2026-06-19T15:29:01.392013+00:00] question_answered: Answered question Q-INT-001
2. [2026-06-19T15:29:01.392028+00:00] question_answered: Answered question Q-INT-002
3. [2026-06-19T15:29:01.392041+00:00] question_answered: Answered question Q-INT-003
4. [2026-06-19T15:29:01.392051+00:00] question_answered: Answered question Q-INT-004
5. [2026-06-19T15:29:01.392061+00:00] question_answered: Answered question Q-INT-005
6. [2026-06-19T15:29:01.392140+00:00] evidence_collected: Collected CLI evidence for: show dial-peer voice summary
7. [2026-06-19T15:29:01.392159+00:00] evidence_collected: Collected CLI evidence for: show sip-ua status
8. [2026-06-19T15:29:01.392174+00:00] evidence_collected: Collected CLI evidence for: debug ccsip messages
