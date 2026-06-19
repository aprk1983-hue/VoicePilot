# VP-CUBE-0001: Outbound Calls Fail

**Category:** Cisco CUBE  
**Topology:** Cisco CUCM → Cisco CUBE → ITSP  
**DSL Source:** [`plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml`](../../plugins/cisco/playbooks/cube/vp-cube-0001-outbound-calls-fail.vpb.yaml)  
**DSL Version:** 1.0.0  
**Status:** Active

> The authoritative machine-readable playbook is the `.vpb.yaml` file above. This document is a human-readable summary. VoicePilot Playbook Engine loads the DSL file at case bind time.

## Symptoms

- Users cannot make outbound PSTN calls
- Internal calls may work
- Calls may fail with fast busy
- SIP errors may include 404, 403, 408, 488, 503

## Business Impact

High. Users cannot call external numbers.

## Investigation Approach

This playbook investigates like TAC — it does **not** assume root cause. Investigation proceeds through:

1. Intake and scope clarification
2. Topology validation (CUCM → CUBE → ITSP)
3. Low-cost evidence first (`show sip-ua status`, `show dial-peer voice summary`)
4. SIP debug to discriminate hypothesis branches
5. Targeted configuration collection based on findings
6. Confidence-gated root cause confirmation (≥85 required; ≥95 for high-confidence closure)
7. Verified resolution with rollback guidance

## Initial Questions

- Did this ever work before?
- When did it stop working?
- Was anything changed recently?
- Are all outbound calls failing?
- Is it only international, mobile, or specific number ranges?
- Are inbound calls working?
- Is only one site affected?
- Which provider is used?

## Required Commands

- `show dial-peer voice summary`
- `show sip-ua status`
- `show run | sec dial-peer`
- `show run | sec voice service voip`
- `show call active voice brief`
- `show logging`

## Logs Required

- `debug ccsip messages` (capture one failing call; disable after)

## Hypothesis Branches

1. Dial-peer mismatch
2. Translation rule issue
3. Provider routing issue
4. SIP trunk unavailable
5. Codec mismatch
6. DNS issue
7. TLS/certificate issue
8. Firewall/network timeout
9. Calling number/caller ID rejected
10. Provider fraud/geographic blocking

## Evidence Rules (Summary)

| Signal | Interpretation |
|--------|----------------|
| SIP 404 generated locally | Dial-peer or translation issue on CUBE |
| SIP 503 from provider | Provider rejection or service issue |
| SIP 488 / SDP mismatch | Codec negotiation failure |
| SIP 408 | Network, firewall, or DNS timeout |
| DNS failure | Provider FQDN resolution problem |
| TLS handshake failure | Certificate or TLS profile issue |
| No matching outbound dial-peer | Dial-peer gap for destination class |
| Translation changes called number | Translation rule distortion |

## Confidence Rules

- **Below 85:** Continue investigation — next best action required; root cause blocked
- **85+:** Root cause confirmation permitted if mandatory evidence complete and no major contradiction
- **95+:** High confidence — requires multiple independent supporting findings

## Verification

- Test local outbound call
- Test mobile outbound call
- Test international outbound call (if in scope)
- Confirm inbound still works
- Confirm trunk registered (`show sip-ua status`)
- Confirm no new CUBE errors

## Related Documentation

- [VoicePilot DSL Specification](../../docs/dsl/voicepilot-dsl.md)
- [Canonical Data Model](../../docs/data-model/canonical-data-model.md)
