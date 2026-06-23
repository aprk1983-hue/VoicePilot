"""Bootstrap default VKF knowledge packs for runtime evaluation."""

from __future__ import annotations

from pathlib import Path

from knowledge.knowledge_engine import KnowledgeEngine
from knowledge.knowledge_loader import KnowledgeLoader
from knowledge.knowledge_registry import KnowledgeRegistry

PACKS_ROOT = Path(__file__).resolve().parents[2] / "knowledge" / "packs"

_default_registry: KnowledgeRegistry | None = None


def load_default_knowledge_packs(
    registry: KnowledgeRegistry | None = None,
) -> KnowledgeRegistry:
    """Load all bundled YAML knowledge packs into a registry."""
    active_registry = registry or KnowledgeRegistry()
    loader = KnowledgeLoader(registry=active_registry)

    if PACKS_ROOT.is_dir():
        for path in sorted(PACKS_ROOT.rglob("*.yaml")):
            if path.is_file():
                loader.load_file(path)

    return active_registry


def default_knowledge_engine() -> KnowledgeEngine:
    """Return a knowledge engine backed by bundled default packs."""
    global _default_registry
    if _default_registry is None:
        _default_registry = load_default_knowledge_packs()
    return KnowledgeEngine(_default_registry)


def reset_default_knowledge_engine() -> None:
    """Clear cached default registry (for tests)."""
    global _default_registry
    _default_registry = None
