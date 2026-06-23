# Genesys Cloud Investigation Engine v1

Sprint 14.4 delivers the deterministic Genesys Cloud investigation pipeline reusing the existing VoicePilot engines.

## Playbook

**ID:** `VP-GENESYS-0001`

**Path:** `plugins/genesys/playbooks/cloud/vp-genesys-0001-genesys-cloud-investigation.vpb.yaml`

## Architecture

Reuses without modification:

- RuntimeEngine
- Hypothesis Engine
- Correlation Engine
- Recommendation Engine
- Discovery Planner
- Investigation Quality
- Engineering Knowledge Framework (EKF)
- Engineering Change Package
- Enterprise Reporting
- Brain Engine
- Validation Engine

## Hypotheses (27)

| Category | Hypotheses |
|----------|------------|
| Authentication / Access | OAuth failure, Token expired, Organization unavailable |
| Infrastructure | Edge offline, Edge degraded, Conversation service unavailable, Analytics service unavailable |
| Voice Routing | BYOC Cloud trunk unavailable, BYOC Premises Edge unavailable, SIP OPTIONS failure, Carrier unreachable, TLS certificate expired, TLS negotiation failure |
| Queues / Agents | Queue unavailable, Queue member unavailable, Queue overloaded, Agent not logged in, Agent stuck interacting, Presence synchronization issue, User routing disabled |
| Architect / Integrations | Architect flow failure, Architect publish issue, Data Action failure |
| Media / Recording | WebRTC failure, Media service unavailable, Recording failure |
| Campaigns | Outbound campaign failure |

## Correlation Rules (10)

1. OAuth failure + token expired → Authentication root cause
2. Edge offline + BYOC Premises unavailable → Edge infrastructure root cause
3. BYOC trunk unavailable + SIP OPTIONS failure → Trunk / carrier root cause
4. TLS expired + TLS negotiation failure → TLS root cause
5. Queue unavailable + queue member unavailable → Queue staffing / routing root cause
6. Agent not logged in + presence sync failure → Agent availability root cause
7. Architect publish failure + flow failure → Architect flow root cause
8. Data Action failure + flow failure → Integration root cause
9. Media service unavailable + WebRTC failure → Media infrastructure root cause
10. Carrier unreachable + SIP OPTIONS failure → Trunk path root cause

## Discovery Commands

- `organization-export`
- `users-export`
- `queues-export`
- `queue-members-export`
- `agents-export`
- `presence-export`
- `flows-export`
- `architect-export`
- `data-actions-export`
- `byoc-cloud-trunks-export`
- `byoc-premises-trunks-export`
- `edge-devices-export`
- `recording-policies-export`
- `campaigns-export`
- `skills-export`

## Knowledge References

Recommendations and change packages reference:

- `VP-GENESYS-CLOUD-RB-001` … `VP-GENESYS-CLOUD-RB-010` (advisory runbooks)
- `VP-GENESYS-CLOUD-VG-001` … `VP-GENESYS-CLOUD-VG-010` (verification guides)
- `VP-GENESYS-CLOUD-REF-001` … `VP-GENESYS-CLOUD-REF-005` (references)

## Scenario Pack

`examples/sample_evidence/scenarios/vp_genesys_0001/` — 12 regression scenarios:

- `oauth_failure`
- `edge_offline`
- `byoc_cloud_trunk_unavailable`
- `byoc_premises_edge_unavailable`
- `sip_options_failure`
- `tls_certificate_expired`
- `queue_unavailable`
- `agent_not_logged_in`
- `architect_flow_failure`
- `data_action_failure`
- `webrtc_media_failure`
- `outbound_campaign_failure`

Each scenario includes `expected_result.yaml`, evidence exports, and `golden_report.md`.

## CLI

```bash
voicepilot investigate VP-GENESYS-0001
voicepilot scenarios VP-GENESYS-0001
voicepilot plan-scenario VP-GENESYS-0001 --scenario queue_unavailable
voicepilot quality-scenario VP-GENESYS-0001 --scenario edge_offline
voicepilot report-scenario VP-GENESYS-0001 --scenario tls_certificate_expired --type executive
voicepilot change-package-scenario VP-GENESYS-0001 --scenario agent_not_logged_in
voicepilot validate VP-GENESYS-0001
```

## Constraints

- Read-only investigation
- Evidence-only — uploaded exports only
- Advisory recommendations and change packages only
- No OAuth, REST, GraphQL, or live Genesys connectivity
- No configuration changes

## Related Tests

- `tests/test_genesys_investigation_engine.py`
- `tests/test_vp_genesys_0001_scenarios.py`
