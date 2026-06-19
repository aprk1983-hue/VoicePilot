# VoicePilot Brain — System Architecture

## Overview

The VoicePilot Brain is the structured intelligence and orchestration layer that powers VoicePilot AI. It is not a chatbot. It is an AI Voice Operations Engineer that investigates incidents with the discipline of a senior Cisco TAC engineer: explicit state, evidence-backed reasoning, confidence-gated conclusions, and enterprise-grade documentation.

The Brain is composed of sixteen cooperating engines governed by a canonical State Machine and unified by a single Case State model. The engineer is always in control.

## Design Principles

| Principle | Description |
|-----------|-------------|
| Evidence Before Conclusion | No root cause without cited evidence |
| Structured State Over Conversation | Case State is the source of truth, not chat history |
| Never Guess | Reasoning Engine eliminates; it does not speculate |
| Confidence Gates | Confidence Engine blocks premature confirmation |
| Institutional Knowledge | Knowledge and Learning Engines build enterprise corpus, not model weights |
| Lifecycle Discipline | State Machine enforces TAC investigation phases |
| Auditability | Every decision traceable to inputs, rules, and artifacts |
| Engineer in Control | VoicePilot recommends; the engineer approves and acts |
| Low Risk First | Cost Optimizer prioritizes high-information, low-disruption actions |
| Graph-Based Reasoning | Investigation Graph stores relationships, not just text |

## Architecture

```
                              ┌─────────────────────────────────┐
                              │      Investigation Engine       │
                              │   (Orchestrator / Case Owner)   │
                              └───────────────┬─────────────────┘
                                              │
                              ┌───────────────▼─────────────────┐
                              │      Investigation Planner        │
                              │   (Strategic Controller)          │
                              └───────────────┬─────────────────┘
                                              │
                              ┌───────────────▼─────────────────┐
                              │         State Machine           │
                              │   (Lifecycle Constitution)      │
                              └───────────────┬─────────────────┘
                                              │
    ┌──────────┬──────────┬──────────┬────────┼────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼        ▼        ▼          ▼          ▼
Question   Evidence  Reasoning Confidence Playbook Topology  Knowledge   Cost
 Engine     Engine    Engine    Engine    Engine   Engine     Engine   Optimizer
    │          │          │          │        │        │          │          │
    └──────────┴──────────┴──────────┴────────┴────────┴──────────┴──────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            Decision Engine          Investigation Graph        Timeline Engine
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                              ┌─────────────────────────────────┐
                              │         Report Engine             │
                              └───────────────┬─────────────────┘
                                              │
                              ┌───────────────▼─────────────────┐
                              │        Learning Engine            │
                              └─────────────────────────────────┘
```

## Module Index

### Orchestration & Lifecycle

| Module | Role |
|--------|------|
| [Investigation Engine](investigation-engine/README.md) | Orchestrates every investigation; owns Case State |
| [Investigation Planner](investigation-planner/README.md) | Strategic controller — strategy, proof objectives, engine dispatch |
| [State Machine](state-machine/README.md) | Governs lifecycle states and transition gates |

### Reasoning & Evidence

| Module | Role |
|--------|------|
| [Reasoning Engine](reasoning-engine/README.md) | Hypothesis generation, ranking, and elimination |
| [Evidence Engine](evidence-engine/README.md) | Forensic evidence tracking and quality assessment |
| [Confidence Engine](confidence-engine/README.md) | Scoring, explanation, and confirmation thresholds |
| [Investigation Graph](investigation-graph/README.md) | Graph-based reasoning model with typed nodes and edges |
| [Decision Engine](decision-engine/README.md) | Immutable audit ledger of every technical decision |

### Investigation Execution

| Module | Role |
|--------|------|
| [Question Engine](question-engine/README.md) | TAC-style question selection by information gain |
| [Cost Optimizer](cost-optimizer/README.md) | Low-risk, high-information action prioritization |
| [Playbook Engine](playbook-engine/README.md) | Vendor investigation playbook selection and guidance |
| [Topology Engine](topology-engine/README.md) | Voice infrastructure modeling and path analysis |

### Knowledge & Memory

| Module | Role |
|--------|------|
| [Knowledge Engine](knowledge-engine/README.md) | Curated voice platform and operations knowledge |
| [Learning Engine](learning-engine/README.md) | Structured post-incident organizational knowledge |
| [Timeline Engine](timeline-engine/README.md) | Authoritative chronological investigation timeline |

### Deliverables

| Module | Role |
|--------|------|
| [Report Engine](report-engine/README.md) | Enterprise incident and RCA documentation |

## VoicePilot DSL Dependency

Investigation playbooks are authored in the [VoicePilot DSL](../docs/dsl/voicepilot-dsl.md) (`.vpb.yaml`). The **Playbook Engine** loads DSL playbooks, validates them, and binds them to active cases. At runtime, DSL definitions are materialized into canonical objects: **Case** (symptom defaults, playbook binding), **Question** (intake and discrimination), **Evidence** (requirements and artifacts), **Hypothesis** (seeds), **Recommendation** and **InvestigationStep** (next-best-action and collection), **Verification** (checklist steps), and **Report** (section templates). Rule blocks drive **Decision**, **ConfidenceScore**, and **InvestigationGraph** edge creation through the Reasoning, Decision, Confidence, and Evidence engines.

## Canonical Data Model Dependency

All Brain engines communicate through typed canonical objects defined in the [VoicePilot Canonical Data Model](../docs/data-model/canonical-data-model.md). The **Case** object is the root aggregate. Engines do not exchange free text as system of record — they read and write structured objects including Evidence, Hypothesis, Decision, Question, Topology, TimelineEvent, Recommendation, ConfidenceScore, InvestigationGraph, and related artifacts.

The Investigation Engine is the sole mutation authority for Case-scoped objects. Child objects always carry a `case_id` reference. Evidence links to source artifacts (LogArtifact, Configuration). Hypotheses declare supporting and contradicting evidence. Decisions document rejected alternatives. Recommendations include verification and rollback guidance where applicable. Root cause confirmation requires evidence linkage and a passing confidence gate.

## Case State — Single Source of Truth

All engines read from and write to the canonical Case State through the Investigation Engine. No engine maintains conflicting parallel state. The Case State fields below map to the canonical object model.

```yaml
case_id:
status:                 # State Machine lifecycle state
severity:
business_impact:
symptom:
affected_scope:
platform:
topology:               # Topology Engine
timeline:               # Timeline Engine
recent_changes:
known_facts:
missing_evidence:       # Evidence Engine
evidence:               # Evidence Engine
hypotheses:             # Reasoning Engine
investigation_graph:    # Investigation Graph
decisions:              # Decision Engine
strategy:               # Investigation Planner
confidence:             # Confidence Engine
next_best_action:       # Cost Optimizer + Investigation Planner
root_cause:
resolution:
verification:
preventive_action:
lessons_learned:
```

## Investigation Lifecycle

```
NEW → INTAKE → DISCOVERY → TOPOLOGY → COLLECTION → ANALYSIS
  → HYPOTHESIS → INVESTIGATION → RESOLUTION → VERIFICATION
  → LEARNING → CLOSED
```

See [State Machine](state-machine/README.md) for entry conditions, exit conditions, and failure gates.

## MVP Scenario

**Topology:** Cisco CUCM → Cisco CUBE → ITSP

**Playbook:** VP-CUBE-0001 — Outbound Calls Fail

**Flow:**
1. Investigation Engine opens case; Playbook Engine binds VP-CUBE-0001
2. Investigation Planner selects Routing-first strategy with proof objectives
3. Cost Optimizer ranks questions and show commands ahead of debug and captures
4. Question Engine drives intake; Topology Engine models call path
5. Evidence Engine collects CLI and debug artifacts; Timeline Engine records events
6. Reasoning Engine generates and eliminates hypotheses; Investigation Graph links evidence to hypotheses
7. Decision Engine records every elimination and confirmation with alternatives
8. Confidence Engine gates root cause confirmation
9. Report Engine produces RCA; Learning Engine captures structured knowledge
10. State Machine advances to CLOSED

## Core Rule

**VoicePilot must never provide a final root cause unless it can show evidence.**

This rule is enforced by the Reasoning Engine (no guess), Evidence Engine (provenance required), Confidence Engine (threshold gate), Decision Engine (evidence-linked decisions), and Investigation Graph (support chain validation).

## Document Convention

Each module document contains: Purpose, Responsibilities, Inputs, Outputs, Internal State, Interactions With Other Engines, MVP Workflow, Future Extensions, Failure Modes, and Design Principles.

---

*VoicePilot Brain Architecture — Sprint 0, Day 4*
*Review status: Draft for Distinguished Engineer review*
