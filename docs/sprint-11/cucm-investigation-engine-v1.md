# Cisco CUCM Investigation Engine v1

Sprint 11.3 extends the VoicePilot deterministic investigation pipeline to support Cisco Unified Communications Manager (CUCM) using **uploaded evidence only**. VoicePilot remains read-only — it never connects to CUCM, executes AXL, SSH, or applies configuration changes.

## Playbook

| Field | Value |
|-------|-------|
| ID | `VP-CUCM-0001` |
| Title | Cisco CUCM Investigation |
| Path | `plugins/cisco/playbooks/cucm/vp-cucm-0001-cisco-cucm-investigation.vpb.yaml` |

## Evidence Types

Deterministic parsers support:

| Command | Parser |
|---------|--------|
| `show risdb query phone` | RIS Database |
| `utils dbreplication runtimestate` | DB Replication |
| `utils service list` | Service Status |
| `show cert list` | Certificate Status |
| `show route plan` | Route Plan |
| `show sip trunk` | SIP Trunk / Device Registration |

Additional evidence types listed in the playbook (network cluster, device, perf query, status) are declared for collection guidance; parsers can be extended in future sprints.

## Canonical Voice Objects (CVOM)

CUCM types in `core/model/cucm_objects.py`:

- `CUCMCluster`, `CUCMNode`, `Phone`, `SIPTrunk`, `Gateway`
- `RoutePattern`, `RouteList`, `RouteGroup`, `CallingSearchSpace`, `Partition`
- `DevicePool`, `Region`, `Location`
- `MediaResourceGroup`, `MediaResourceGroupList`, `MediaTerminationPoint`, `Transcoder`, `ConferenceBridge`

## Topology Relationships

`RelationshipBuilder` infers:

- Phone `REGISTERED_TO` CUCMNode
- Phone `USES` DevicePool / CSS
- DevicePool `USES` Region / Location
- CSS `USES` Partition
- RoutePattern `ROUTES_TO` RouteList → RouteGroup → Gateway → SIPTrunk → Provider

## Health Rules

Ten CUCM rules in `core/health/cucm_rules.py`:

Phone not registered, DB replication unhealthy, CallManager stopped, TFTP stopped, certificate expired, SIP trunk down, RIS unavailable, route pattern missing, CSS missing, partition missing.

## Hypotheses and Correlation

Rules in `core/runtime/cucm_investigation.py`:

| Hypothesis | Key Signal |
|------------|------------|
| Phone registration failure | `phone_not_registered` |
| Database replication issue | `db_replication_unhealthy` |
| CallManager service failure | `callmanager_service_stopped` |
| TFTP issue | `tftp_service_stopped` |
| Certificate issue | `certificate_expired` |
| SIP trunk issue | `sip_trunk_down` |
| Routing configuration issue | `route_pattern_missing` |
| CSS mismatch | `css_missing` |
| Partition mismatch | `partition_missing` |
| Media resource issue | `media_resource_unavailable` |

Correlation rules reinforce replication + registration, CallManager + registration, CSS/partition + routing, and certificate + TLS failures.

## Recommendations and Change Package

Recommendations reference the Cisco CUCM Professional Pack (`VP-CISCO-CUCM-RB-*`, `VP-CISCO-CUCM-VG-*`). The Engineering Change Package engine selects CUCM action plans and advisory templates when `playbook_id == VP-CUCM-0001`.

## Scenarios

`examples/sample_evidence/scenarios/vp_cucm_0001/`:

| Scenario | Expected Root Cause | Min Confidence |
|----------|---------------------|----------------|
| `phone_not_registered` | Phone registration failure | 88 |
| `sip_trunk_down` | SIP trunk issue | 89 |
| `db_replication` | Database replication issue | 92 |
| `callmanager_service_down` | CallManager service failure | 94 |
| `certificate_expired` | Certificate issue | 91 |

## CLI

```bash
voicepilot investigate VP-CUCM-0001
voicepilot scenarios VP-CUCM-0001
voicepilot report-scenario VP-CUCM-0001 --scenario phone_not_registered --type executive
voicepilot change-package-scenario VP-CUCM-0001 --scenario phone_not_registered
```

## Tests

- `tests/test_cucm_investigation_engine.py` — parsers, CVOM, topology, health, hypotheses, correlation, recommendations, change package, CLI
- `tests/test_vp_cucm_0001_scenarios.py` — scenario regression (root cause, confidence, PASS)

## Related Documentation

- [CUCM Professional Pack v1](cucm-professional-pack-v1.md)
- [Architecture — CUCM Investigation Pipeline](../../architecture/part-4-platform/06-cucm-investigation-pipeline.md)
