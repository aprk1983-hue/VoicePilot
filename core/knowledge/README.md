# Voice Knowledge Framework (VKF)

Vendor-neutral knowledge pack loading, validation, registration, and evaluation for VoicePilot.

## Purpose

Externalize operational guidance, best practices, and vendor notes into structured YAML packs instead of embedding knowledge in core code.

## Layout

| Module | Responsibility |
|--------|----------------|
| `knowledge_severity.py` | `KnowledgeSeverity` enum |
| `knowledge_categories.py` | `KnowledgeCategory` enum |
| `knowledge_models.py` | `KnowledgePack`, `KnowledgeMatch` |
| `knowledge_schema.py` | YAML schema validation |
| `knowledge_pack.py` | Pack construction helpers |
| `knowledge_registry.py` | Pack registration and lookup |
| `knowledge_loader.py` | YAML loading |
| `knowledge_matcher.py` | Object-to-pack matching |
| `knowledge_engine.py` | Evaluation orchestration |
| `knowledge_report.py` | Aggregated report model |

## Usage

```python
from knowledge import KnowledgeEngine, KnowledgeLoader

loader = KnowledgeLoader()
loader.load_directory(packs_root / "cisco")
engine = KnowledgeEngine(registry=loader.registry)
report = engine.evaluate_case(case)
```

## Related

- [VKF v1 spec](../../docs/sprint-7/knowledge-framework-v1.md)
- [CVOM](../model/README.md)
