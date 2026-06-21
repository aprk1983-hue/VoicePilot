# Engineering Knowledge Framework (EKF)

The `engineering_knowledge` package connects Engineering Asset Framework (EAF)
assets into explainable, traversable engineering knowledge.

## Principles

- Sits on top of `engineering_assets`
- Deterministic matching and graph traversal
- In-memory only in v1
- No vendor-specific logic in the framework core

## Usage

```python
from engineering_knowledge import EngineeringKnowledgeEngine, EngineeringKnowledgeRegistry

registry = EngineeringKnowledgeRegistry()
engine = EngineeringKnowledgeEngine(knowledge_registry=registry)
report = engine.evaluate_case(case)
```

See [Engineering Knowledge Framework v1](../../docs/sprint-10/engineering-knowledge-framework-v1.md).
