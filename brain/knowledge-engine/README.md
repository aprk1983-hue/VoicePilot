# Knowledge Engine

## Purpose

The Knowledge Engine is the curated, structured intelligence layer of VoicePilot. It stores authoritative voice operations knowledge — not conversational memory, not model weights — in a form that investigation engines can query with deterministic expectations. It enables VoicePilot to reason like a senior TAC engineer who has internalized product documentation, field notices, and years of case history.

This engine separates **what is known about voice platforms** from **what is known about a specific incident**. Incident facts live in Case State; platform facts live here.

## Responsibilities

- Maintain versioned, searchable knowledge corpora across voice vendors and protocols.
- Serve factual retrieval to Investigation, Reasoning, Question, Evidence, Playbook, and Topology engines.
- Encode configuration rules, CLI command libraries, and diagnostic interpretation guidance.
- Store RFC decisions, architectural standards, and product design constraints.
- Maintain playbook metadata, symptom-to-playbook mappings, and investigation best practices.
- Track known bugs, field notices, and version compatibility matrices.
- Store security knowledge: TLS requirements, certificate practices, SRTP policies, toll fraud indicators.
- Enforce knowledge provenance: source, version, effective date, and deprecation status.
- Prevent stale or superseded knowledge from influencing active investigations without explicit override.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Knowledge Artifacts | Content Curators / Import Pipelines | Playbooks, CLI libraries, configuration rules, RFCs |
| Vendor Documentation | Cisco, Microsoft, ITSP References | Product guides, release notes, compatibility bulletins |
| Field Intelligence | Learning Engine | Anonymized case patterns, confirmed root causes, verification outcomes |
| Deprecation Notices | Engineering / Operations | Retired rules, superseded playbooks, obsolete software versions |
| Query Requests | All Brain Engines | Structured lookups by platform, symptom, command, error code, topology element |
| Context Filters | Investigation Engine | Platform version, topology type, active playbook, affected component |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Knowledge Facts | Reasoning, Question, Evidence Engines | Deterministic facts with source attribution |
| CLI Command Recommendations | Evidence Engine, Investigation Engine | Commands appropriate to platform and investigation phase |
| Configuration Rules | Reasoning Engine, Topology Engine | Valid configuration patterns and anti-patterns |
| Interpretation Rules | Evidence Engine | How to read SIP response codes, syslog patterns, dial-peer states |
| Playbook Metadata | Playbook Engine | Playbook catalog, applicability criteria, vendor tags |
| Known Bug Matches | Reasoning Engine | Bug ID, affected versions, workaround, fixed-in version |
| Compatibility Assertions | Topology Engine | Supported version pairs, known interoperability constraints |
| Security Guidance | Reasoning Engine, Investigation Engine | Certificate requirements, encryption policies, fraud indicators |
| RFC Constraints | All Engines | Architectural decisions that bound investigation behavior |

## Internal State

- **Knowledge Corpus Index** — partitioned stores: Cisco, Microsoft Teams, SIP/RTP, Security, Playbooks, RFCs.
- **Version Graph** — software version nodes with compatibility edges and known defect attachments.
- **Rule Registry** — configuration rules and evidence interpretation rules with priority and scope tags.
- **Command Library** — CLI commands indexed by platform, privilege level, output type, and investigation phase.
- **Provenance Ledger** — source document, author, review date, effective range, deprecation flag per artifact.
- **Retrieval Cache** — short-lived query result cache keyed by investigation context hash.
- **Symptom Index** — inverted index mapping symptoms and error signatures to playbooks and knowledge articles.

### Knowledge Domains

| Domain | Contents |
|--------|----------|
| Cisco Knowledge | CUCM, CUBE, Expressway, IOS voice features, dial plans, SIP trunks |
| Microsoft Teams Knowledge | Direct Routing, SBC pairs, normalization, emergency calling |
| RFC Knowledge | VoicePilot architectural decisions and investigation constraints |
| Playbooks | Structured investigation procedures per vendor and scenario |
| Best Practices | TAC investigation methodology, evidence standards, escalation criteria |
| CLI Commands | Show, debug, and test commands with expected output patterns |
| Configuration Rules | Valid trunk configs, dial-peer patterns, codec policies |
| Known Bugs | CSC references, field notices, version-specific defects |
| Version Compatibility | Supported upgrade paths, known broken combinations |
| Security Knowledge | TLS, SRTP, certificate chains, toll fraud, ACL requirements |

## Interactions

- **Investigation Engine** — queries knowledge during every phase for commands, rules, and escalation guidance.
- **Reasoning Engine** — retrieves interpretation rules, known bugs, and root cause patterns to constrain hypothesis generation.
- **Evidence Engine** — obtains command templates, expected output schemas, and parsing rules.
- **Question Engine** — retrieves intake question banks, symptom clarifiers, and topology discovery prompts.
- **Playbook Engine** — loads playbook definitions and applicability metadata from the playbook corpus.
- **Topology Engine** — retrieves component models, valid relationships, and reference architectures.
- **Confidence Engine** — retrieves evidence quality standards and minimum evidence requirements per root cause class.
- **Learning Engine** — writes anonymized, structured case intelligence back into the knowledge corpus after closure.

## Future Extensions

- Multi-tenant knowledge isolation with shared global corpus and tenant-specific overlays.
- Knowledge approval workflow with SME review gates before publication.
- Automated ingestion from vendor release notes and bug scrub databases.
- Graph-based knowledge linking: symptom → component → command → interpretation → root cause.
- Regional and provider-specific knowledge packs (ITSP quirks, regulatory requirements).
- Knowledge freshness scoring and automatic investigation warnings when corpus is outdated.
- Integration with external CMDB and asset inventory for version-aware retrieval.

## Example Workflow

**Scenario:** Investigation of outbound PSTN failure on Cisco CUBE.

1. **Playbook Binding** — Playbook Engine queries Knowledge Engine for playbooks matching symptom "outbound PSTN failure" and platform "Cisco CUBE". Returns `VP-CUBE-0001` with metadata.

2. **Command Retrieval** — Evidence Engine requests required commands for CUBE outbound investigation. Knowledge Engine returns: `show dial-peer voice summary`, `show sip-ua status`, `show run | sec dial-peer`, `debug ccsip messages` with privilege requirements and output parsing hints.

3. **Interpretation Rule Lookup** — Engineer submits SIP trace showing `404 Not Found`. Evidence Engine queries interpretation rules. Knowledge Engine returns: "404 generated locally on CUBE often indicates dial-peer mismatch or translation rule failure" with confidence weighting guidance.

4. **Known Bug Check** — Reasoning Engine queries known bugs for CUBE version 16.12.4 with symptom signature. Knowledge Engine returns no exact match; investigation proceeds without bug shortcut.

5. **Configuration Rule Validation** — Topology Engine submits dial-peer configuration excerpt. Knowledge Engine validates pattern syntax, destination URI format, and codec list against CUBE best practices. Returns one warning: progressive dial-peer numbering gap may cause unintended match.

6. **Learning Writeback** — After case closure, Learning Engine submits anonymized pattern: "404 local + missing mobile dial-peer." Knowledge Engine indexes as a field intelligence artifact linked to `VP-CUBE-0001`, pending SME review.
