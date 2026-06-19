# Investigation Graph

## Purpose

The Investigation Graph stores investigation reasoning as an explicit graph — not as free text, not as chat history. Nodes represent investigation entities (symptoms, evidence, hypotheses, decisions, and more). Edges represent typed relationships (supports, contradicts, eliminates, confirms). This structure makes reasoning auditable, queryable, and comparable across similar incidents.

A senior TAC engineer mentally connects symptoms to evidence to hypotheses to conclusions. The Investigation Graph makes that mental model persistent and machine-traversable.

## Responsibilities

- Construct and maintain a directed graph per investigation case.
- Create typed nodes for all investigation entities.
- Create typed edges expressing relationships between entities.
- Synchronize graph updates from Reasoning, Evidence, Decision, and other engines.
- Support graph queries: "what evidence supports this hypothesis?", "what eliminated this cause?"
- Enable similarity comparison between investigation graphs across cases.
- Provide graph traversals for Report Engine RCA narrative generation.
- Detect orphaned nodes and inconsistent edge semantics.
- Version graph snapshots at major milestones for audit replay.
- Feed Learning Engine with anonymized graph patterns for recurrence matching.

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Entity Creation Events | All Brain Engines | New symptoms, evidence, hypotheses, decisions, etc. |
| Relationship Assertions | Reasoning, Decision, Evidence Engines | Supports, contradicts, eliminates, confirms |
| Topology Model | Topology Engine | Topology component nodes and relationships |
| Question Records | Question Engine | Question nodes linked to answers and facts |
| Resolution Package | Investigation Engine | Root cause, solution, verification nodes |
| Graph Schema | Knowledge Engine | Valid node types, edge types, cardinality rules |
| Similarity Queries | Learning Engine | Historical graph patterns for comparison |

## Outputs

| Output | Consumer | Description |
|--------|----------|-------------|
| Investigation Graph | Case State | Canonical graph per case |
| Graph Queries | Reasoning Engine, Report Engine | Traversal results |
| Support Chains | Confidence Engine | Evidence-to-hypothesis-to-conclusion paths |
| Elimination Chains | Report Engine | Decision-to-hypothesis elimination paths |
| Similarity Scores | Learning Engine | Graph comparison with historical cases |
| Orphan Alerts | Investigation Engine | Nodes without required edges |
| Graph Snapshot | Timeline Engine, Audit | Point-in-time graph at milestones |
| Visualization Model | Engineer Interface (future) | Structured graph for review UI |

## Internal State

- **Graph Store** — nodes and edges per `case_id`.
- **Node Registry** — all nodes with type, attributes, creation timestamp, source engine.
- **Edge Registry** — all edges with type, source node, target node, confidence, evidence ref.
- **Schema Validator** — enforces valid node/edge types and cardinality.
- **Snapshot Archive** — milestone graph versions.
- **Similarity Index** — graph fingerprint for cross-case comparison (anonymized).
- **Traversal Cache** — frequent query results cached per graph version.

### Node Types

| Node Type | Description | Example |
|-----------|-------------|---------|
| `symptom` | Reported failure manifestation | Outbound PSTN fast busy |
| `environment` | Platform and deployment context | CUBE 16.12.4, single site |
| `topology_component` | Infrastructure element | CUBE dmz-cube-01 |
| `evidence` | Collected artifact | E-002 SIP debug |
| `hypothesis` | Candidate root cause | Dial-peer mismatch |
| `question` | Investigative question | Are only mobile numbers failing? |
| `decision` | Recorded technical decision | DEC-003 eliminate provider rejection |
| `root_cause` | Confirmed root cause | Mobile dial-peer gap |
| `solution` | Applied fix | Added dial-peer 201 |
| `verification` | Post-fix validation | Mobile outbound test pass |

### Edge Types

| Edge Type | Semantics | Example |
|-----------|-----------|---------|
| `supports` | Source increases likelihood of target | E-002 supports HYP-DP-001 |
| `contradicts` | Source decreases likelihood of target | E-001 contradicts HYP-TRUNK-DOWN |
| `requires` | Target cannot be resolved without source | HYP-DP-001 requires E-005 |
| `eliminates` | Source rules out target | DEC-003 eliminates HYP-PROVIDER |
| `confirms` | Source confirms target | DEC-006 confirms ROOT-CAUSE-001 |
| `depends_on` | Source depends on target | E-005 depends_on TOPO-CUBE |
| `caused_by` | Target was caused by source | ROOT-CAUSE-001 caused_by CHANGE-DP-EDIT |

### Graph Fragment Example

```
[symptom: outbound failure]
        │
        ▼ depends_on
[topology_component: CUBE] ◄── depends_on ── [evidence: E-005 dial-peer config]
        │
        ▼ supports
[hypothesis: dial-peer mismatch] ── contradicts ── [evidence: E-001 trunk UP]
        │
        ▼ supports
[evidence: E-002 local 404]
        │
        ▼ eliminates
[decision: DEC-003 eliminate provider rejection]
        │
        ▼ confirms
[root_cause: mobile dial-peer gap]
        │
        ▼ caused_by
[environment: dial-peer edit yesterday]
        │
        ▼ depends_on
[solution: add dial-peer 201]
        │
        ▼ confirms
[verification: mobile test pass]
```

## Interactions With Other Engines

- **Reasoning Engine** — creates hypothesis nodes; asserts supports/contradicts edges from evidence.
- **Evidence Engine** — creates evidence nodes; links to hypotheses and topology components.
- **Decision Engine** — creates decision nodes; asserts eliminates/confirms edges.
- **Topology Engine** — creates topology_component nodes; environment context nodes.
- **Question Engine** — creates question nodes; links to known_facts and hypotheses.
- **Investigation Engine** — creates symptom, root_cause, solution, verification nodes.
- **Investigation Planner** — strategy nodes (future) linked to proof objectives.
- **Confidence Engine** — traverses support chains to validate conclusion paths.
- **Timeline Engine** — graph snapshots at milestones referenced in timeline.
- **Report Engine** — traverses graph for RCA narrative and evidence citation chains.
- **Learning Engine** — receives anonymized graph fingerprints; supplies similarity matches.
- **Cost Optimizer** — may use graph gaps to identify high-value collection targets.

## MVP Workflow for VP-CUBE-0001: Outbound Calls Fail

1. **Case Open** — Graph initialized. Node: `symptom` (outbound PSTN failure). Node: `environment` (CUCM → CUBE → ITSP).

2. **Topology** — Nodes: `topology_component` CUCM, CUBE, ITSP. Edges: CUCM `depends_on` CUBE `depends_on` ITSP.

3. **Evidence Collection** — Nodes: E-001, E-002, E-005. Edge: E-001 `contradicts` HYP-TRUNK-DOWN. Edge: E-002 `supports` HYP-DP-001. Edge: E-002 `contradicts` HYP-PROVIDER.

4. **Hypothesis Generation** — Nodes: HYP-DP-001 (dial-peer mismatch), HYP-PROVIDER, HYP-TRUNK-DOWN, HYP-CODEC.

5. **Decisions** — Nodes: DEC-002, DEC-003, DEC-006. Edge: DEC-002 `eliminates` HYP-TRUNK-DOWN. Edge: DEC-003 `eliminates` HYP-PROVIDER. Edge: DEC-006 `confirms` ROOT-CAUSE-001.

6. **Root Cause** — Node: `root_cause` (mobile dial-peer gap). Edge: CHANGE-DP-EDIT `caused_by` ROOT-CAUSE-001. Edge: E-005 `supports` ROOT-CAUSE-001.

7. **Resolution** — Node: `solution` (add dial-peer). Node: `verification` (mobile test pass). Edge: solution `confirms` verification.

8. **Similarity** — On closure, graph fingerprint compared to Learning Engine. Match found with prior case L-0042 (same symptom → local 404 → dial-peer gap pattern).

## Future Extensions

- Graph diff between investigation milestones for progress visualization.
- Automated subgraph extraction for executive summary (symptom → root cause path only).
- Cross-case graph merge for recurring incident pattern detection.
- Graph-based hypothesis seeding: import subgraph from similar historical case as candidates only.
- Formal graph validation: ensure every root_cause node has at least one support chain to evidence.
- Graph export in standard formats for external analytics platforms.
- Multi-case investigation graph linking for widespread outages.
- Probabilistic edge weights evolving as evidence accumulates.

## Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Orphan hypothesis | Hypothesis with no evidence edges | Orphan detector alerts; Reasoning Engine must link or eliminate |
| Unsupported root cause node | Conclusion without support chain | Schema validator blocks root_cause without `supports` path from evidence |
| Contradictory edges | Both supports and eliminates without resolution | Consistency checker flags; Decision Engine supersession required |
| Graph drift from Case State | Graph and state out of sync | Synchronization contract: engines update graph and state atomically via Investigation Engine |
| Over-connected graph | Noise edges reduce query value | Edge creation requires source engine authorization and evidence ref |
| Similarity false positive | Wrong historical case matched | Similarity is advisory only; Reasoning Engine still requires fresh evidence |

## Design Principles

1. **Graph, not text** — Reasoning relationships are first-class edges, not prose buried in chat.
2. **Typed semantics** — Edge types have defined meaning; arbitrary relationships are prohibited.
3. **Evidence anchoring** — Every path to root_cause must traverse evidence nodes.
4. **Never guess** — Hypothesis nodes remain unconfirmed until `confirms` edge from decision or evidence chain.
5. **State maintained** — Graph is part of Case State, versioned and persistent.
6. **Comparable incidents** — Graph structure enables cross-case similarity without sharing raw evidence.
7. **Engineer in control** — Engineer may dispute edges; disputes create decision nodes.
8. **Auditable traversals** — Any RCA claim must be reproducible as a graph traversal query.
