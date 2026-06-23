# AudioCodes SBC Investigation Engine v1

Sprint 13.4 delivers the deterministic AudioCodes SBC investigation pipeline reusing the existing VoicePilot engines.

## Playbook

**ID:** `VP-AUDIOCODES-0001`

**Path:** `plugins/audiocodes/playbooks/sbc/vp-audiocodes-0001-audiocodes-sbc-investigation.vpb.yaml`

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

## Hypotheses (15)

| ID | Title |
|----|-------|
| HYP-AUDIOCODES-PROVIDER | Provider SIP service unavailable |
| HYP-AUDIOCODES-SIP-OPTIONS | SIP OPTIONS failure |
| HYP-AUDIOCODES-PROXY | Proxy Set unavailable |
| HYP-AUDIOCODES-IP-GROUP | IP Group disabled |
| HYP-AUDIOCODES-ROUTING | Routing configuration issue |
| HYP-AUDIOCODES-TLS-CERT | TLS certificate expired |
| HYP-AUDIOCODES-TLS-NEG | TLS negotiation failure |
| HYP-AUDIOCODES-MEDIA-REALM | Media Realm failure |
| HYP-AUDIOCODES-RTP | RTP path issue |
| HYP-AUDIOCODES-ONEWAY | One-way audio |
| HYP-AUDIOCODES-CODEC | Codec negotiation issue |
| HYP-AUDIOCODES-LICENSE | License exhaustion |
| HYP-AUDIOCODES-HA-SYNC | HA synchronization issue |
| HYP-AUDIOCODES-GATEWAY | Gateway unreachable |
| HYP-AUDIOCODES-DNS | DNS resolution failure |

## Correlation Rules (6)

1. SIP OPTIONS + Provider 503 → Provider outage
2. TLS expired + TLS negotiation failure → TLS root cause
3. IP Group disabled + Routing failure → Routing configuration issue
4. Media Realm down + One-way audio → Media infrastructure issue
5. License exhausted + Call failures → Capacity issue
6. HA sync failure + Standby active → HA degradation

## Discovery Commands

- `show voip status`
- `show sip-options`
- `show proxy-set`
- `show ip-group`
- `show routing-table`
- `show media-realm`
- `show tls-context`
- `show certificates`
- `show ha-status`
- `show licenses`

## Scenario Pack

`examples/sample_evidence/scenarios/vp_audiocodes_0001/` — 10 regression scenarios:

- `sip_options_failed`
- `provider_503`
- `proxy_set_unavailable`
- `ip_group_disabled`
- `routing_rule_missing`
- `tls_certificate_expired`
- `media_realm_down`
- `rtp_one_way_audio`
- `session_license_exhausted`
- `ha_sync_failure`

Each scenario includes `expected_result.yaml`, evidence files, and `golden_report.md`.

## CLI

```bash
voicepilot investigate VP-AUDIOCODES-0001
voicepilot scenarios VP-AUDIOCODES-0001
voicepilot scenarios VP-AUDIOCODES-0001 --scenario sip_options_failed
voicepilot report-scenario VP-AUDIOCODES-0001 --scenario tls_certificate_expired --type executive
voicepilot change-package-scenario VP-AUDIOCODES-0001 --scenario ip_group_disabled
voicepilot plan-scenario VP-AUDIOCODES-0001 --scenario routing_rule_missing
voicepilot quality-scenario VP-AUDIOCODES-0001 --scenario proxy_set_unavailable
voicepilot validate VP-AUDIOCODES-0001
```

## Constraints

- Read-only investigation
- Deterministic evidence-only analysis
- No SSH, REST, SNMP, or live SBC connectivity
- Advisory recommendations and change packages only
- No configuration changes performed by VoicePilot

## Tests

- `tests/test_audiocodes_investigation_engine.py`
- `tests/test_vp_audiocodes_0001_scenarios.py`

## Related Documentation

- [AudioCodes Knowledge Library](audiocodes-professional-pack-v1.md)
- [AudioCodes Parser Framework](audiocodes-parser-framework-v1.md)
- [AudioCodes Health Rules](audiocodes-health-rules-v1.md)
- [Architecture: AudioCodes Investigation Engine](../../architecture/part-4-platform/15-audiocodes-investigation-engine.md)
