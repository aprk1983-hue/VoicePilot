# 19 — Genesys Cloud Investigation Engine

> **Status:** Implemented

## Purpose

Document the Genesys Cloud Investigation Engine: deterministic end-to-end investigation using uploaded export evidence and GVOM objects.

## Repository Modules Involved

- [`../../plugins/genesys/playbooks/cloud/`](../../plugins/genesys/playbooks/cloud/) — VP-GENESYS-0001 playbook
- [`../../core/runtime/genesys_investigation.py`](../../core/runtime/genesys_investigation.py) — hypotheses, correlation, action plans
- [`../../core/runtime/intake_summary.py`](../../core/runtime/intake_summary.py) — intake handoff
- [`../../core/discovery/genesys_planner_rules.py`](../../core/discovery/genesys_planner_rules.py) — discovery planner rules
- [`../../core/health/genesys_rules.py`](../../core/health/genesys_rules.py) — health evaluation
- [`../../plugins/genesys/parser/cloud/`](../../plugins/genesys/parser/cloud/) — evidence parsers
- [`../../core/runtime/scenario_runner.py`](../../core/runtime/scenario_runner.py) — scenario regression

## Pipeline Diagram

```text
VP-GENESYS-0001 Playbook → Intake → Evidence → Parsers → GVOM
  → HypothesisEngine → CorrelationEngine → DiscoveryPlanner
  → InvestigationQuality → RecommendationEngine → ChangePackage → ReportEngine
```

## Object Flow

```text
Export Evidence → ParserEngine → GVOM (Organization, Queue, Agent, EdgeDevice, ByocCloudTrunk, ...)
  → TopologyBuilder → HealthEngine → AnalysisFindings
```

## Evidence Flow

```text
organization-export / queues-export / agents-export / edge-devices-export
  / byoc-cloud-trunks-export / flows-export / data-actions-export / campaigns-export
  → Parser signals → Hypothesis rules → Correlation boosts → Recommendations
```

## Decision Flow

```text
Parser signals → HypothesisRule match → Ranked hypotheses
  → CorrelationRule reinforcement → Top hypothesis
  → Action plan (VP-GENESYS-CLOUD-RB-*) → ECP advisory package
```

## Knowledge Flow

```text
Hypothesis signals → EKF asset matching → VP-GENESYS-CLOUD-000001..000025
  → VP-GENESYS-CLOUD-RB-* runbooks → VP-GENESYS-CLOUD-VG-* verification
  → VP-GENESYS-CLOUD-REF-* references → Report / Change Package
```

## Scenario Matrix

| Scenario | Expected Root Cause | Key Signals |
|----------|---------------------|-------------|
| oauth_failure | OAuth failure | oauth_failure, token_expired |
| edge_offline | Edge offline | edge_offline |
| byoc_cloud_trunk_unavailable | BYOC Cloud trunk unavailable | byoc_cloud_trunk_failure |
| byoc_premises_edge_unavailable | BYOC Premises Edge unavailable | byoc_premises_edge_unavailable, edge_offline |
| sip_options_failure | SIP OPTIONS failure | sip_options_failure |
| tls_certificate_expired | TLS certificate expired | tls_certificate_expired, tls_negotiation_failure |
| queue_unavailable | Queue unavailable | queue_unavailable |
| agent_not_logged_in | Agent not logged in | agent_not_logged_in |
| architect_flow_failure | Architect flow failure | call_flow_failure, architect_publish_failure |
| data_action_failure | Data Action failure | data_action_failure, call_flow_failure |
| webrtc_media_failure | Media service unavailable | media_service_unavailable, webrtc_failure |
| outbound_campaign_failure | Outbound campaign failure | outbound_campaign_failure |

## Hypotheses

27 deterministic hypotheses covering authentication, infrastructure, voice routing, queues/agents, Architect integrations, media/recording, and campaigns.

## Scenario Pack

`examples/sample_evidence/scenarios/vp_genesys_0001/` — 12 regression scenarios with `expected_result.yaml` and `golden_report.md`.

## Constraints

- Read-only investigation
- Advisory recommendations and change packages only
- No OAuth, REST, GraphQL, or live Genesys connectivity
- Vendor-specific logic in Genesys modules only

## Related Tests

- [`../../tests/test_genesys_investigation_engine.py`](../../tests/test_genesys_investigation_engine.py)
- [`../../tests/test_vp_genesys_0001_scenarios.py`](../../tests/test_vp_genesys_0001_scenarios.py)

## Related Documentation

- [`../../docs/sprint-14/genesys-investigation-engine-v1.md`](../../docs/sprint-14/genesys-investigation-engine-v1.md)
- [17 — Genesys Cloud Object Model](17-genesys-object-model.md)
- [18 — Genesys Cloud Health Engine](18-genesys-health-engine.md)

## Cross References

- [02 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [03 — Topology Engines](../part-3-engines/03-topology-engines.md)
