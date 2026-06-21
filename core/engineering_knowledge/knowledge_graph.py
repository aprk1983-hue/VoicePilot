"""Knowledge graph over engineering assets and knowledge entries."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from engineering_assets.asset_registry import EngineeringAssetRegistry
from engineering_assets.asset_relationships import EngineeringRelationshipRegistry
from engineering_knowledge.knowledge_exceptions import KnowledgeGraphNodeNotFoundError
from engineering_knowledge.knowledge_models import KnowledgeRelationshipType
from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
from engineering_knowledge.knowledge_relationships import KnowledgeRelationshipRegistry


@dataclass(frozen=True)
class KnowledgeGraphEdge:
    """Directed edge in the engineering knowledge graph."""

    source_id: str
    target_id: str
    relationship_type: str
    edge_class: str


@dataclass(frozen=True)
class KnowledgeGraphTraversal:
    """Result of a graph traversal."""

    start_node: str
    visited_nodes: tuple[str, ...]
    edges: tuple[KnowledgeGraphEdge, ...]
    strategy: str


class EngineeringKnowledgeGraph:
    """Graph connecting engineering assets and knowledge through typed relationships."""

    _PARENT_TYPES = frozenset(
        {
            KnowledgeRelationshipType.SUPERSEDES.value,
            KnowledgeRelationshipType.IMPLEMENTS.value,
        }
    )
    _DEPENDENCY_TYPES = frozenset({KnowledgeRelationshipType.DEPENDS_ON.value})
    _REFERENCE_TYPES = frozenset({KnowledgeRelationshipType.REFERENCES.value})
    _RELATED_TYPES = frozenset(
        {
            KnowledgeRelationshipType.RELATED.value,
            KnowledgeRelationshipType.SIMILAR_TO.value,
            KnowledgeRelationshipType.KNOWN_WITH.value,
            KnowledgeRelationshipType.VERIFIES.value,
            KnowledgeRelationshipType.CAUSES.value,
            KnowledgeRelationshipType.RESOLVES.value,
        }
    )

    def __init__(
        self,
        knowledge_registry: EngineeringKnowledgeRegistry,
        asset_registry: EngineeringAssetRegistry,
        knowledge_relationships: KnowledgeRelationshipRegistry | None = None,
        asset_relationships: EngineeringRelationshipRegistry | None = None,
    ) -> None:
        self._knowledge_registry = knowledge_registry
        self._asset_registry = asset_registry
        self._knowledge_relationships = knowledge_relationships or KnowledgeRelationshipRegistry()
        self._asset_relationships = asset_relationships or EngineeringRelationshipRegistry()

    def node_exists(self, node_id: str) -> bool:
        """Return whether a node exists in the graph."""
        return self._knowledge_registry.exists(node_id) or self._asset_registry.exists(node_id)

    def parents(self, node_id: str) -> tuple[str, ...]:
        """Return parent nodes for a graph node."""
        self._ensure_node(node_id)
        parents: set[str] = set()
        for edge in self._outgoing_edges(node_id):
            if edge.relationship_type in self._PARENT_TYPES:
                parents.add(edge.target_id)
        for edge in self._incoming_edges(node_id):
            if edge.relationship_type in self._PARENT_TYPES:
                parents.add(edge.source_id)
            if edge.relationship_type == KnowledgeRelationshipType.SUPERSEDES.value:
                parents.add(edge.source_id)
        return tuple(sorted(parents))

    def children(self, node_id: str) -> tuple[str, ...]:
        """Return child nodes for a graph node."""
        self._ensure_node(node_id)
        children: set[str] = set()
        for edge in self._outgoing_edges(node_id):
            if edge.relationship_type == KnowledgeRelationshipType.SUPERSEDES.value:
                children.add(edge.target_id)
            if edge.relationship_type in self._PARENT_TYPES:
                children.add(edge.target_id)
        for edge in self._incoming_edges(node_id):
            if edge.relationship_type in self._PARENT_TYPES:
                children.add(edge.source_id)
        return tuple(sorted(children))

    def dependencies(self, node_id: str) -> tuple[str, ...]:
        """Return dependency nodes for a graph node."""
        self._ensure_node(node_id)
        values: set[str] = set()
        for edge in self._outgoing_edges(node_id):
            if edge.relationship_type in self._DEPENDENCY_TYPES:
                values.add(edge.target_id)
        return tuple(sorted(values))

    def references(self, node_id: str) -> tuple[str, ...]:
        """Return referenced nodes for a graph node."""
        self._ensure_node(node_id)
        values: set[str] = set()
        for edge in self._outgoing_edges(node_id):
            if edge.relationship_type in self._REFERENCE_TYPES:
                values.add(edge.target_id)
        for knowledge in self._knowledge_registry.list_knowledge():
            if node_id in knowledge.asset_ids:
                values.update(knowledge.asset_ids)
        if self._asset_registry.exists(node_id):
            asset = self._asset_registry.get(node_id)
            values.update(asset.references)
            values.update(asset.related_asset_ids)
        return tuple(sorted(item for item in values if item != node_id))

    def related(self, node_id: str) -> tuple[str, ...]:
        """Return related nodes for a graph node."""
        self._ensure_node(node_id)
        values: set[str] = set()
        for edge in self._outgoing_edges(node_id) + self._incoming_edges(node_id):
            if edge.relationship_type in self._RELATED_TYPES:
                values.add(edge.target_id if edge.source_id == node_id else edge.source_id)
        return tuple(sorted(values))

    def traverse_depth_first(self, start_node: str, *, max_depth: int = 5) -> KnowledgeGraphTraversal:
        """Traverse the graph depth-first with cycle protection."""
        return self._traverse(start_node, strategy="depth-first", max_depth=max_depth)

    def traverse_breadth_first(self, start_node: str, *, max_depth: int = 5) -> KnowledgeGraphTraversal:
        """Traverse the graph breadth-first with cycle protection."""
        return self._traverse(start_node, strategy="breadth-first", max_depth=max_depth)

    def _traverse(
        self,
        start_node: str,
        *,
        strategy: str,
        max_depth: int,
    ) -> KnowledgeGraphTraversal:
        self._ensure_node(start_node)
        visited: list[str] = []
        edges: list[KnowledgeGraphEdge] = []
        seen: set[str] = set()

        if strategy == "breadth-first":
            queue: deque[tuple[str, int]] = deque([(start_node, 0)])
            while queue:
                node_id, depth = queue.popleft()
                if node_id in seen:
                    continue
                seen.add(node_id)
                visited.append(node_id)
                if depth >= max_depth:
                    continue
                for edge in self._outgoing_edges(node_id):
                    edges.append(edge)
                    if edge.target_id not in seen:
                        queue.append((edge.target_id, depth + 1))
        else:
            stack: list[tuple[str, int]] = [(start_node, 0)]
            while stack:
                node_id, depth = stack.pop()
                if node_id in seen:
                    continue
                seen.add(node_id)
                visited.append(node_id)
                if depth >= max_depth:
                    continue
                for edge in reversed(self._outgoing_edges(node_id)):
                    edges.append(edge)
                    if edge.target_id not in seen:
                        stack.append((edge.target_id, depth + 1))

        return KnowledgeGraphTraversal(
            start_node=start_node,
            visited_nodes=tuple(visited),
            edges=tuple(edges),
            strategy=strategy,
        )

    def _outgoing_edges(self, node_id: str) -> tuple[KnowledgeGraphEdge, ...]:
        edges: list[KnowledgeGraphEdge] = []
        if self._knowledge_registry.exists(node_id):
            knowledge = self._knowledge_registry.get(node_id)
            for asset_id in knowledge.asset_ids:
                if self._asset_registry.exists(asset_id):
                    edges.append(
                        KnowledgeGraphEdge(
                            source_id=node_id,
                            target_id=asset_id,
                            relationship_type=KnowledgeRelationshipType.REFERENCES.value,
                            edge_class="references",
                        )
                    )
        for relationship in self._knowledge_relationships.list_relationships():
            if relationship.source_knowledge_id == node_id:
                edges.append(
                    KnowledgeGraphEdge(
                        source_id=relationship.source_knowledge_id,
                        target_id=relationship.target_knowledge_id,
                        relationship_type=relationship.relationship_type.value,
                        edge_class=_edge_class(relationship.relationship_type),
                    )
                )
        if self._asset_registry.exists(node_id):
            for relationship in self._asset_relationships.list_relationships():
                if relationship.source_asset == node_id:
                    edges.append(
                        KnowledgeGraphEdge(
                            source_id=relationship.source_asset,
                            target_id=relationship.target_asset,
                            relationship_type=relationship.relationship_type.value,
                            edge_class=_asset_edge_class(relationship.relationship_type.value),
                        )
                    )
        return tuple(sorted(edges, key=lambda edge: (edge.target_id, edge.relationship_type)))

    def _incoming_edges(self, node_id: str) -> tuple[KnowledgeGraphEdge, ...]:
        edges: list[KnowledgeGraphEdge] = []
        for relationship in self._knowledge_relationships.list_relationships():
            if relationship.target_knowledge_id == node_id:
                edges.append(
                    KnowledgeGraphEdge(
                        source_id=relationship.source_knowledge_id,
                        target_id=relationship.target_knowledge_id,
                        relationship_type=relationship.relationship_type.value,
                        edge_class=_edge_class(relationship.relationship_type),
                    )
                )
        if self._asset_registry.exists(node_id):
            for relationship in self._asset_relationships.list_relationships():
                if relationship.target_asset == node_id:
                    edges.append(
                        KnowledgeGraphEdge(
                            source_id=relationship.source_asset,
                            target_id=relationship.target_asset,
                            relationship_type=relationship.relationship_type.value,
                            edge_class=_asset_edge_class(relationship.relationship_type.value),
                        )
                    )
        return tuple(sorted(edges, key=lambda edge: (edge.source_id, edge.relationship_type)))

    def _ensure_node(self, node_id: str) -> None:
        if not self.node_exists(node_id):
            raise KnowledgeGraphNodeNotFoundError(node_id)


def _edge_class(relationship_type: KnowledgeRelationshipType) -> str:
    if relationship_type == KnowledgeRelationshipType.DEPENDS_ON:
        return "dependencies"
    if relationship_type == KnowledgeRelationshipType.REFERENCES:
        return "references"
    if relationship_type in {
        KnowledgeRelationshipType.SUPERSEDES,
        KnowledgeRelationshipType.IMPLEMENTS,
    }:
        return "parents"
    return "related"


def _asset_edge_class(relationship_type: str) -> str:
    if relationship_type in {"REQUIRES", "REFERENCES"}:
        return "dependencies" if relationship_type == "REQUIRES" else "references"
    return "related"
