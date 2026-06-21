# Engineering Knowledge Framework v1

## Purpose

The Engineering Asset Framework (EAF) defines how engineering knowledge assets are modeled, registered, linked, and searched. The Engineering Knowledge Framework (EKF) sits on top of EAF and connects those assets into explainable knowledge that can be matched to live investigation context.

EKF v1 delivers the reusable framework only. Vendor libraries such as Cisco incidents or Microsoft articles are future content layers built on EAF + EKF.

## Architecture

```text
Future Vendor Libraries (content only)
                │
                ▼
Engineering Knowledge Framework (EKF)
                │
                ▼
Engineering Asset Framework (EAF)
                │
                ▼
VoicePilot Runtime / Cases / Health / Topology
```

Core components:

| Module | Responsibility |
|--------|----------------|
| `knowledge_models.py` | Immutable knowledge, match, relationship, recommendation models |
| `knowledge_registry.py` | In-memory knowledge registry |
| `knowledge_relationships.py` | Knowledge-to-knowledge relationship registry |
| `knowledge_graph.py` | Asset + knowledge graph with DFS/BFS traversal |
| `knowledge_matcher.py` | Deterministic matching to assets, objects, health, findings |
| `knowledge_engine.py` | Evaluation and search API |
| `knowledge_report.py` | Markdown knowledge reports |

## Knowledge Graph

`EngineeringKnowledgeGraph` connects:

- knowledge entries
- linked engineering assets
- knowledge relationships
- asset relationships from EAF

Graph views:

- `parents()`
- `children()`
- `dependencies()`
- `references()`
- `related()`

Traversal:

- `traverse_depth_first()`
- `traverse_breadth_first()`

Both strategies include cycle protection via visited-node tracking.

## Matching

`EngineeringKnowledgeMatcher` accepts:

- engineering assets
- canonical voice objects
- health results
- investigation findings

Matching is deterministic and ranked by score:

1. Asset/tag linkage
2. Finding signal overlap
3. Voice object type overlap
4. Health rule identifier overlap

No AI. No embeddings.

## Relationships

EKF relationship types:

- `RELATED`
- `DEPENDS_ON`
- `REFERENCES`
- `SUPERSEDES`
- `VERIFIES`
- `IMPLEMENTS`
- `CAUSES`
- `RESOLVES`
- `SIMILAR_TO`
- `KNOWN_WITH`

These are separate from EAF asset relationship types and model explainable knowledge links.

## Knowledge Engine

`EngineeringKnowledgeEngine` provides:

- `evaluate_case(case)`
- `evaluate_topology(topology)`
- `evaluate_health(health_report)`
- `evaluate_findings(findings)`

Search helpers:

- `find_related_knowledge(knowledge_id)`
- `find_verification_guides()`
- `find_runbooks()`
- `find_references(knowledge_id)`
- `find_related_incidents()`

## Knowledge Report

Markdown sections:

- Summary
- Matched knowledge
- Related assets
- Recommended reading
- Verification guides
- Runbooks
- References

## Example Usage

```python
from engineering_knowledge import EngineeringKnowledgeEngine, EngineeringKnowledgeRegistry

registry = EngineeringKnowledgeRegistry()
engine = EngineeringKnowledgeEngine(knowledge_registry=registry)

report = engine.evaluate_case(case)
print(engine.format_report(report))
```

## Future AI Integration

When AI retrieval is added, it should sit above EKF:

1. EKF performs deterministic matching and graph expansion
2. Optional AI ranking or summarization operates on the filtered result set

EKF remains the source of truth for knowledge identity, relationships, and explainability.

## Future Vendor Libraries

Vendor-specific libraries will register:

- EAF assets (runbooks, guides, incidents, articles)
- EKF knowledge entries and relationships

Examples:

- Cisco incident packs
- Microsoft Teams knowledge packs
- AudioCodes and Genesys operational libraries

Those libraries must not add vendor logic to EKF core.

## Current Limitations

- In-memory only
- Simple deterministic ranking
- No persistence or REST API yet
- No incident libraries included in v1

## Package Location

- Implementation: `core/engineering_knowledge/`
- Import: `from engineering_knowledge import EngineeringKnowledgeEngine`
