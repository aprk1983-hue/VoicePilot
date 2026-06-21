"""Engineering Knowledge Framework — explainable knowledge over engineering assets."""

from engineering_knowledge.knowledge_engine import (
    EngineeringKnowledgeEngine,
    evaluate_case_with_topology,
)
from engineering_knowledge.knowledge_exceptions import (
    DuplicateEngineeringKnowledgeError,
    DuplicateKnowledgeRelationshipError,
    EngineeringKnowledgeError,
    EngineeringKnowledgeNotFoundError,
    KnowledgeGraphNodeNotFoundError,
    KnowledgeRelationshipNotFoundError,
)
from engineering_knowledge.knowledge_graph import (
    EngineeringKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphTraversal,
)
from engineering_knowledge.knowledge_matcher import EngineeringKnowledgeMatcher
from engineering_knowledge.knowledge_models import (
    EngineeringKnowledge,
    KnowledgeMatch,
    KnowledgeRecommendation,
    KnowledgeRelationship,
    KnowledgeRelationshipType,
    KnowledgeReport,
)
from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
from engineering_knowledge.knowledge_relationships import KnowledgeRelationshipRegistry
from engineering_knowledge.knowledge_report import (
    build_knowledge_report,
    build_recommendations_from_assets,
    format_knowledge_report_markdown,
)

__all__ = [
    "DuplicateEngineeringKnowledgeError",
    "DuplicateKnowledgeRelationshipError",
    "EngineeringKnowledge",
    "EngineeringKnowledgeEngine",
    "EngineeringKnowledgeError",
    "EngineeringKnowledgeGraph",
    "EngineeringKnowledgeMatcher",
    "EngineeringKnowledgeNotFoundError",
    "EngineeringKnowledgeRegistry",
    "KnowledgeGraphEdge",
    "KnowledgeGraphNodeNotFoundError",
    "KnowledgeGraphTraversal",
    "KnowledgeMatch",
    "KnowledgeRecommendation",
    "KnowledgeRelationship",
    "KnowledgeRelationshipNotFoundError",
    "KnowledgeRelationshipRegistry",
    "KnowledgeRelationshipType",
    "KnowledgeReport",
    "build_knowledge_report",
    "build_recommendations_from_assets",
    "evaluate_case_with_topology",
    "format_knowledge_report_markdown",
]
