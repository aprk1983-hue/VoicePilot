# Cisco CUCM Professional Pack v1

## Purpose

Sprint 11.2 delivers production-quality Cisco Unified Communications Manager (CUCM) engineering assets built through the Engineering Asset Factory (EAF²). All assets pass factory validation and achieve quality scores of 90 or higher.

## Asset Inventory

| Type | Count | ID Range |
|------|-------|----------|
| Incidents | 25 | `VP-CISCO-CUCM-000001` – `VP-CISCO-CUCM-000025` |
| Runbooks | 10 | `VP-CISCO-CUCM-RB-001` – `VP-CISCO-CUCM-RB-010` |
| Verification Guides | 10 | `VP-CISCO-CUCM-VG-001` – `VP-CISCO-CUCM-VG-010` |
| References | 5 | `VP-CISCO-CUCM-REF-001` – `VP-CISCO-CUCM-REF-005` |
| **Total** | **50** | |

## Incident Categories

### Phone Registration (000001–000005)

- Phone not registered
- Registration rejected
- Unknown device
- Duplicate MAC
- TFTP unreachable

### SIP Trunks (000006–000010)

- SIP trunk down
- OPTIONS failure
- TLS failure
- 488 codec mismatch
- DNS resolution failure

### Routing (000011–000015)

- CSS partition mismatch
- Partition access mismatch
- Route pattern missing
- Route list failure
- Route group unavailable

### Media (000016–000020)

- Region codec mismatch
- Location CAC blocking
- Missing MTP
- Missing transcoder
- MRGL resource issue

### Cluster (000021–000025)

- Database replication issue
- CallManager service stopped
- TFTP service stopped
- Tomcat certificate issue
- ITL/CTL mismatch

## Runbooks

| ID | Name |
|----|------|
| RB-001 | RB-CUCM-PHONE-REGISTRATION |
| RB-002 | RB-CUCM-SIP-TRUNK |
| RB-003 | RB-CUCM-CSS |
| RB-004 | RB-CUCM-TFTP |
| RB-005 | RB-CUCM-REPLICATION |
| RB-006 | RB-CUCM-MTP |
| RB-007 | RB-CUCM-REGION |
| RB-008 | RB-CUCM-LOCATION |
| RB-009 | RB-CUCM-CERTIFICATE |
| RB-010 | RB-CUCM-ROUTE-PATTERN |

## Verification Guides

| ID | Name |
|----|------|
| VG-001 | VG-CUCM-RIS |
| VG-002 | VG-CUCM-SIP |
| VG-003 | VG-CUCM-TFTP |
| VG-004 | VG-CUCM-DB |
| VG-005 | VG-CUCM-CERT |
| VG-006 | VG-CUCM-MEDIA |
| VG-007 | VG-CUCM-DEVICE |
| VG-008 | VG-CUCM-CSS |
| VG-009 | VG-CUCM-ROUTING |
| VG-010 | VG-CUCM-SERVICES |

## References

| ID | Title |
|----|-------|
| REF-001 | Cisco Unified Communications SRND |
| REF-002 | Cisco Collaboration SRND |
| REF-003 | Cisco SIP Trunk Guide |
| REF-004 | Cisco RIS Guide |
| REF-005 | Cisco Certificate Guide |

## Relationships

Each incident links to:

- One or more runbooks (`VP-CISCO-CUCM-RB-*`)
- One or more verification guides (`VP-CISCO-CUCM-VG-*`)
- One or more references (`VP-CISCO-CUCM-REF-*`)

EAF² relationship generation produces typed edges for navigation and quality scoring.

## Quality Statistics

All 50 CUCM professional pack assets:

- Pass `EngineeringAssetFactory.validate_assets()`
- Score **≥ 90/100** on deterministic quality criteria
- Include required incident metadata: symptoms, findings, causes, resolution, rollback, verification

Validate locally:

```bash
voicepilot assets validate
voicepilot assets quality
voicepilot assets stats
```

## Location

```text
knowledge/incidents/cisco/cucm/
knowledge/runbooks/cisco/cucm/
knowledge/verification/cisco/cucm/
knowledge/references/cisco/cucm/
```
