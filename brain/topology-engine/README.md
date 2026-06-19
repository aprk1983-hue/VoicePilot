# Topology Engine

## Purpose

The Topology Engine builds and maintains the voice infrastructure model for every investigation. It transforms engineer descriptions, configuration artifacts, and knowledge templates into a structured, reusable topology graph that represents how calls flow from endpoints through platforms to PSTN. Topology is not a diagram asset; it is an operational model that drives evidence targeting, hypothesis scoping, and playbook selection.

A senior TAC engineer mentally models the call path before asking for a single show command. This engine makes that model explicit, validated, and persistent.

## Responsibilities

- Construct voice topology models from intake answers, configuration excerpts, and evidence.
- Represent supported platform types: CUCM, CUBE, Expressway, Microsoft Teams, SBC, firewall, provider, voice gateway, PSTN.
- Model call paths: signaling path, media path, and policy enforcement points.
- Validate topology completeness against investigation requirements.
- Identify topology gaps that block evidence collection or hypothesis scoping.
- Support topology reuse: reference architectures and prior case topology templates.
- Track per-component attributes: hostname, role, version, zone, trunk bindings.
- Detect topology inconsistencies and contradictions.
- Provide path analysis: which components lie on the affected call path.
- Export topology context to Reasoning, Evidence, Playbook, and Question engines.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Intake & Discovery Answers | Question Engine | Site layout, platform inventory, provider identity |
| Configuration Artifacts | Evidence Engine | Trunk configs, dial-peers, route patterns, SBC profiles |
| Knowledge Templates | Knowledge Engine | Reference architectures, valid component relationships |
| Engineer Corrections | Investigation Engine | Explicit topology amendments |
| CMDB / Asset Data | External Integration (future) | Device inventory, version, location |
| Prior Case Topology | Learning Engine | Reusable topology patterns for same customer environment |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Topology Model | Case State | Canonical `topology` field |
| Completeness Assessment | State Machine, Investigation Engine | Minimum completeness for phase advancement |
| Topology Gaps | Question Engine | Questions to fill missing elements |
| Path Analysis | Reasoning Engine | Components on affected call path |
| Collection Targets | Evidence Engine | Devices from which to collect evidence |
| Playbook Applicability | Playbook Engine | Topology pattern matching for playbook selection |
| Inconsistency Alerts | Investigation Engine | Contradictions requiring resolution |
| Reusable Topology Template | Learning Engine | Anonymized topology for future cases |

## Internal State

- **Topology Graph** — nodes (components) and edges (signaling, media, policy relationships).
- **Component Registry** — typed instances with attributes and configuration bindings.
- **Reference Template Library** — standard patterns: CUCM→CUBE→ITSP, CUCM→Expressway→CUBE, Teams→SBC→PSTN.
- **Completeness Rules** — per-scenario minimum elements required.
- **Validation Result Cache** — last consistency check outcome.
- **Reuse Index** — customer-environment topology templates keyed by anonymized fingerprint.

### Component Types

| Type | Role in Model |
|------|---------------|
| CUCM | Call control, route patterns, trunk configuration, dial plan origin |
| CUBE | Session border, dial-peers, SIP trunks, codec policy, NAT traversal |
| Expressway | Traversal, B2B/B2C signaling, firewall pinhole coordination |
| Microsoft Teams | Cloud PBX, Direct Routing, normalization, emergency policy |
| SBC | Generic or vendor-specific session border (AudioCodes, Ribbon, etc.) |
| Firewall | Signaling and media pinholes, ALG, inspection policies |
| Provider | ITSP, SIP carrier, PSTN interconnect |
| Voice Gateway | PSTN gateway, PRI/SIP gateway, MGCP devices |
| PSTN | External number space, destination classes (local, mobile, international) |
| Endpoint | Phone, soft client, contact center ingress (when relevant) |

### Topology Graph Structure

```yaml
topology_id:
case_id:
pattern:              # e.g., cucm_cube_itsp, teams_sbc_pstn
components:
  - component_id:
    type:
    role:
    attributes:
      hostname:
      version:
      zone:
    config_bindings: []
relationships:
  - from:
    to:
    type:             # sip_trunk | media_path | route | policy
    attributes:
      trunk_name:
      dial_peer:
      codec:
completeness:
  score:
  missing_elements: []
validation:
  consistent:
  issues: []
```

## Interactions

- **Investigation Engine** — requests topology build, validation, and updates.
- **Question Engine** — receives gap list; topology answers flow back as model updates.
- **Evidence Engine** — receives collection targets; config evidence updates component attributes.
- **Reasoning Engine** — receives path analysis for hypothesis component scoping.
- **Playbook Engine** — topology pattern matching for playbook applicability.
- **Knowledge Engine** — reference architectures and valid relationship rules.
- **State Machine** — completeness gates `TOPOLOGY` → `COLLECTION` transition.
- **Learning Engine** — exports reusable topology templates on case closure.

## Future Extensions

- Automatic topology inference from configuration parsing with engineer validation gate.
- Multi-site topology with location-aware path selection.
- Redundancy modeling: primary/secondary trunks, failover paths.
- Geographic and regulatory overlays (in-country routing, local breakout).
- Real-time topology drift detection against CMDB baseline.
- Graph visualization export for engineer review (supplementary to structured model).
- Cross-investigation topology diff: what changed between incidents.

## Example Workflow

**Scenario:** Outbound PSTN failure. Engineer states CUCM at HQ, CUBE at DMZ, single ITSP.

1. **Template Selection** — Knowledge Engine provides `cucm_cube_itsp` reference template. Topology Engine instantiates graph with placeholder nodes.

2. **Intake Population** — Question answers populate: CUCM `hq-cucm-pub`, CUBE `dmz-cube-01`, provider `CarrierX SIP trunk`.

3. **Gap Detection** — Missing: CUBE dial-peer structure, CUCM route pattern for outbound, trunk binding between CUCM and CUBE. Gaps sent to Question Engine and Evidence Engine.

4. **Evidence Enrichment** — `show run | sec dial-peer` parsed. CUBE component updated with dial-peer list. `show run | sec voice service voip` adds SIP trunk attributes.

5. **Path Analysis** — Outbound call path: Endpoint → CUCM (route pattern 9.X) → SIP trunk to CUBE → dial-peer 9T → ITSP. Reasoning Engine scopes hypotheses to CUBE dial-peer and CUCM route pattern.

6. **Validation** — Consistency check: CUCM trunk destination matches CUBE peer. Pass. Completeness score 85%. State Machine permits `COLLECTION` → `ANALYSIS` progression.

7. **Reuse** — On closure, anonymized topology template stored: "HQ CUCM + DMZ CUBE + CarrierX" for Learning Engine index.
