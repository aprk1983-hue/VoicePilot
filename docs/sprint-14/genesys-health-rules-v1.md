# Genesys Cloud Health Rules v1

## Purpose

Sprint 14.3 delivers deterministic Genesys Cloud health rules evaluated over GVOM objects and topology. Rules integrate with the existing `HealthEngine` and reuse the standard scoring model.

This sprint is **read-only**. Health rules do not generate recommendations or remediation guidance.

## Architecture

```text
GVOM Objects + VoiceTopology
        │
        ▼
HealthEngine (default_health_rule_registry)
        │
        ▼
genesys_rules.py → HealthResult per rule/object
        │
        ▼
HealthReport (overall_score, severity_counts, results)
```

## Rule Inventory (27)

| Category | Rule ID |
|----------|---------|
| Authentication | `genesys_oauth_failure`, `genesys_token_expired`, `genesys_organization_unavailable` |
| Users / Agents | `genesys_agent_not_logged_in`, `genesys_agent_stuck_interacting`, `genesys_presence_sync_failure`, `genesys_user_routing_disabled` |
| Queues | `genesys_queue_unavailable`, `genesys_queue_no_members`, `genesys_queue_member_unavailable`, `genesys_queue_overloaded` |
| Voice Routing | `genesys_byoc_cloud_unavailable`, `genesys_byoc_premises_unavailable`, `genesys_sip_options_failure`, `genesys_carrier_unreachable`, `genesys_tls_certificate_expired`, `genesys_tls_negotiation_failure` |
| Architect | `genesys_architect_publish_failure`, `genesys_data_action_failure` |
| Media | `genesys_media_service_unavailable`, `genesys_webrtc_failure`, `genesys_recording_failure` |
| Campaigns | `genesys_outbound_campaign_failure` |
| Infrastructure | `genesys_edge_offline`, `genesys_edge_degraded`, `genesys_conversation_service_unavailable`, `genesys_analytics_service_unavailable` |

## Evaluation Model

- Each rule returns a `HealthResult` with `PASS` or `FAIL` status
- Severity penalties follow the shared engine model (CRITICAL −30, HIGH −15, MEDIUM −10, LOW −5)
- `recommendation` is always `None` for Genesys rules
- Rules evaluate object `state` fields and evidence `metadata` flags from parsers

## Registration

`register_genesys_health_rules()` is called from `register_builtin_rules()` in `core/health/builtin_rules.py`, so `HealthEngine.evaluate_topology()` and `evaluate_case()` automatically include Genesys rules when GVOM objects are present.

## Constraints

- Read-only, evidence-only evaluation
- No OAuth, REST API, GraphQL, or live Genesys Cloud connectivity
- No recommendations or remediation output
- Deterministic ordering and scoring

## Related Tests

- [`../../tests/test_genesys_health_rules.py`](../../tests/test_genesys_health_rules.py)

## Related Architecture

- [`../../architecture/part-4-platform/18-genesys-health-engine.md`](../../architecture/part-4-platform/18-genesys-health-engine.md)
