# Genesys Cloud Object Model and Parser Framework v1

## Purpose

Sprint 14.2 delivers the Genesys Voice Object Model (GVOM) and a deterministic evidence-only parser framework for Genesys Cloud CX exports. Parsers integrate with the existing `ParserEngine`, `TopologyBuilder`, and `RelationshipBuilder` pipelines.

This sprint is **evidence only**. It does not include OAuth, REST API, GraphQL, live tenant connectivity, health rules, recommendations, or an investigation engine.

## Architecture

```text
Genesys Cloud Export Evidence (CSV / JSON / YAML / TXT)
        │
        ▼
GenesysCloudParser (plugins/genesys/parser/cloud/)
        │
        ▼
GVOM (core/model/genesys_objects.py)
        │
        ▼
TopologyBuilder → RelationshipBuilder
        │
        ▼
CLI (investigate / scenario / report via parser registration)
```

## GVOM Object Types (20)

| Object | Type constant |
|--------|---------------|
| GenesysOrganization | `genesys_organization` |
| GenesysRegion | `genesys_region` |
| EdgeDevice | `genesys_edge_device` |
| ByocCloudTrunk | `genesys_byoc_cloud_trunk` |
| ByocPremisesTrunk | `genesys_byoc_premises_trunk` |
| SipEndpoint | `genesys_sip_endpoint` |
| Queue | `genesys_queue` |
| QueueMember | `genesys_queue_member` |
| Agent | `genesys_agent` |
| PresenceDefinition | `genesys_presence_definition` |
| UserRoutingStatus | `genesys_user_routing_status` |
| Flow | `genesys_flow` |
| ArchitectFlow | `genesys_architect_flow` |
| DataAction | `genesys_data_action` |
| Campaign | `genesys_campaign` |
| WrapUpCode | `genesys_wrap_up_code` |
| RecordingPolicy | `genesys_recording_policy` |
| Recording | `genesys_recording` |
| Division | `genesys_division` |
| Skill | `genesys_skill` |

All GVOM types are frozen dataclasses extending `VoiceObject`.

## Parsers (15)

| Command | Parser ID | Primary GVOM types |
|---------|-----------|-------------------|
| `organization-export` | `genesys_organization_export` | Organization, Region, Division |
| `users-export` | `genesys_users_export` | Agent |
| `queues-export` | `genesys_queues_export` | Queue |
| `queue-members-export` | `genesys_queue_members_export` | QueueMember |
| `agents-export` | `genesys_agents_export` | Agent |
| `presence-export` | `genesys_presence_export` | PresenceDefinition, UserRoutingStatus |
| `flows-export` | `genesys_flows_export` | Flow, WrapUpCode |
| `architect-export` | `genesys_architect_export` | ArchitectFlow |
| `data-actions-export` | `genesys_data_actions_export` | DataAction |
| `byoc-cloud-trunks-export` | `genesys_byoc_cloud_trunks_export` | ByocCloudTrunk, SipEndpoint |
| `byoc-premises-trunks-export` | `genesys_byoc_premises_trunks_export` | ByocPremisesTrunk |
| `edge-devices-export` | `genesys_edge_devices_export` | EdgeDevice |
| `recording-policies-export` | `genesys_recording_policies_export` | RecordingPolicy, Recording |
| `campaigns-export` | `genesys_campaigns_export` | Campaign |
| `skills-export` | `genesys_skills_export` | Skill |

## Parser Features

- **Format detection** — CSV, JSON, YAML, and text key-value exports
- **Schema validation** — required identity fields per parser
- **Unknown field tolerance** — extra columns/keys preserved in metadata
- **Deterministic parsing** — stable record ordering and deduplication (last wins)
- **Finding extraction** — signals aligned with Genesys knowledge pack incidents
- **Evidence metadata** — vendor, command, case_id, format, record_count

## Topology Buckets

`VoiceTopology` partitions Genesys objects into dedicated buckets:

- `genesys_organizations` — Organization, Region
- `genesys_agents` — Agent, PresenceDefinition, UserRoutingStatus
- `genesys_queues` — Queue, QueueMember
- `genesys_flows` — Flow, ArchitectFlow, DataAction, WrapUpCode
- `genesys_trunks` — ByocCloudTrunk, ByocPremisesTrunk, SipEndpoint
- `genesys_edges` — EdgeDevice
- `genesys_campaigns` — Campaign
- `genesys_recordings` — RecordingPolicy, Recording
- `genesys_skills` — Skill
- `genesys_divisions` — Division

## Relationships

`RelationshipBuilder` infers explicit GVOM edges:

| Source | Relationship | Target |
|--------|--------------|--------|
| Agent | `routes_to` | Queue |
| Queue | `provides` | QueueMember |
| Flow | `routes_to` | Queue |
| ArchitectFlow | `uses` | DataAction |
| Campaign | `routes_to` | Queue |
| ByocPremisesTrunk | `connects_to` | EdgeDevice |
| EdgeDevice | `hosted_on` | GenesysOrganization |

## Sample Evidence

Golden samples under `examples/sample_evidence/genesys/`:

- `healthy/` — nominal exports across CSV, JSON, YAML, and TXT
- `failure/` — queue unavailable, edge offline, trunk failure, agent logged out
- `mixed/topology_bundle.json` — multi-object bundle for topology regression

## Registration

Parsers register through `register_genesys_parsers()` and are loaded by `build_default_parser_engine()` in `core/runtime/parser_bootstrap.py`, enabling CLI `investigate`, `scenario`, and `report` flows without additional wiring.

## Constraints

- Read-only, evidence-only investigation
- No REST, OAuth, GraphQL, or live Genesys Cloud connectivity
- Deterministic parsing and relationship inference

## Related Tests

- [`../../tests/test_genesys_parser_framework.py`](../../tests/test_genesys_parser_framework.py)

## Related Architecture

- [`../../architecture/part-4-platform/17-genesys-object-model.md`](../../architecture/part-4-platform/17-genesys-object-model.md)
