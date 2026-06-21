"""Bootstrap bundled engineering knowledge libraries."""

from __future__ import annotations

from pathlib import Path

from engineering_knowledge.knowledge_engine import EngineeringKnowledgeEngine
from engineering_knowledge.knowledge_library_loader import (
    EngineeringKnowledgeLibrary,
    default_knowledge_library_root,
    load_engineering_knowledge_library,
)

_default_library: EngineeringKnowledgeLibrary | None = None
_default_engine: EngineeringKnowledgeEngine | None = None


def load_default_engineering_knowledge_library(
    root: Path | None = None,
) -> EngineeringKnowledgeLibrary:
    """Load bundled engineering knowledge assets from the repository."""
    return load_engineering_knowledge_library(root or default_knowledge_library_root())


def default_engineering_knowledge_library() -> EngineeringKnowledgeLibrary:
    """Return a cached default engineering knowledge library."""
    global _default_library
    if _default_library is None:
        _default_library = load_default_engineering_knowledge_library()
    return _default_library


def default_engineering_knowledge_engine() -> EngineeringKnowledgeEngine:
    """Return an EKF engine backed by bundled Cisco CUBE and future libraries."""
    global _default_engine
    if _default_engine is None:
        library = default_engineering_knowledge_library()
        _default_engine = EngineeringKnowledgeEngine(
            knowledge_registry=library.knowledge_registry,
            asset_registry=library.asset_registry,
            knowledge_relationships=library.relationship_registry,
        )
    return _default_engine


def reset_default_engineering_knowledge_engine() -> None:
    """Clear cached default library and engine (for tests)."""
    global _default_library, _default_engine
    _default_library = None
    _default_engine = None
