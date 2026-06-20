"""Directed dependency traversal over voice topology graphs."""

from __future__ import annotations

from collections import deque

from model.voice_graph import VoiceRelationship
from model.voice_topology import VoiceTopology
from topology.topology_exceptions import TopologyObjectNotFoundError


class DependencyEngine:
    """Traverse directed topology relationships with deterministic, cycle-safe queries."""

    def get_direct_dependencies(
        self,
        topology: VoiceTopology,
        object_id: str,
    ) -> tuple[str, ...]:
        """Return object IDs that ``object_id`` depends on (outgoing edge targets)."""
        _require_object(topology, object_id)
        targets = sorted(
            {
                relationship.target_object_id
                for relationship in topology.relationships
                if relationship.source_object_id == object_id
            }
        )
        return tuple(targets)

    def get_direct_dependents(
        self,
        topology: VoiceTopology,
        object_id: str,
    ) -> tuple[str, ...]:
        """Return object IDs that depend on ``object_id`` (incoming edge sources)."""
        _require_object(topology, object_id)
        sources = sorted(
            {
                relationship.source_object_id
                for relationship in topology.relationships
                if relationship.target_object_id == object_id
            }
        )
        return tuple(sources)

    def get_transitive_dependencies(
        self,
        topology: VoiceTopology,
        object_id: str,
        max_depth: int = 10,
    ) -> tuple[str, ...]:
        """Return all reachable dependency targets up to ``max_depth`` hops."""
        _require_object(topology, object_id)
        outgoing = _outgoing_index(topology)
        return _traverse(
            start_id=object_id,
            adjacency=outgoing,
            max_depth=max_depth,
            neighbor_key=lambda relationship: relationship.target_object_id,
        )

    def get_transitive_dependents(
        self,
        topology: VoiceTopology,
        object_id: str,
        max_depth: int = 10,
    ) -> tuple[str, ...]:
        """Return all reachable dependents up to ``max_depth`` hops."""
        _require_object(topology, object_id)
        incoming = _incoming_index(topology)
        return _traverse(
            start_id=object_id,
            adjacency=incoming,
            max_depth=max_depth,
            neighbor_key=lambda relationship: relationship.source_object_id,
        )

    def explain_dependency_path(
        self,
        topology: VoiceTopology,
        source_id: str,
        target_id: str,
    ) -> tuple[VoiceRelationship, ...]:
        """Return the shortest directed relationship path from source to target."""
        _require_object(topology, source_id)
        _require_object(topology, target_id)
        if source_id == target_id:
            return ()

        outgoing = _outgoing_index(topology)
        queue: deque[tuple[str, list[VoiceRelationship]]] = deque([(source_id, [])])
        visited = {source_id}

        while queue:
            node_id, path = queue.popleft()
            for relationship in outgoing.get(node_id, ()):
                next_id = relationship.target_object_id
                next_path = [*path, relationship]
                if next_id == target_id:
                    return tuple(next_path)
                if next_id in visited:
                    continue
                visited.add(next_id)
                queue.append((next_id, next_path))

        return ()


def _require_object(topology: VoiceTopology, object_id: str) -> None:
    if object_id not in _object_index(topology):
        raise TopologyObjectNotFoundError(object_id)


def _object_index(topology: VoiceTopology) -> dict[str, object]:
    return {obj.id: obj for obj in topology.all_objects()}


def _outgoing_index(topology: VoiceTopology) -> dict[str, tuple[VoiceRelationship, ...]]:
    grouped: dict[str, list[VoiceRelationship]] = {}
    for relationship in topology.relationships:
        grouped.setdefault(relationship.source_object_id, []).append(relationship)

    return {
        source_id: tuple(
            sorted(
                relationships,
                key=lambda item: (item.target_object_id, item.relationship_type, item.relationship_id),
            )
        )
        for source_id, relationships in grouped.items()
    }


def _incoming_index(topology: VoiceTopology) -> dict[str, tuple[VoiceRelationship, ...]]:
    grouped: dict[str, list[VoiceRelationship]] = {}
    for relationship in topology.relationships:
        grouped.setdefault(relationship.target_object_id, []).append(relationship)

    return {
        target_id: tuple(
            sorted(
                relationships,
                key=lambda item: (item.source_object_id, item.relationship_type, item.relationship_id),
            )
        )
        for target_id, relationships in grouped.items()
    }


def _traverse(
    *,
    start_id: str,
    adjacency: dict[str, tuple[VoiceRelationship, ...]],
    max_depth: int,
    neighbor_key,
) -> tuple[str, ...]:
    if max_depth < 1:
        return ()

    visited = {start_id}
    collected: list[str] = []
    frontier = [start_id]

    for _ in range(max_depth):
        if not frontier:
            break

        next_frontier: list[str] = []
        for node_id in sorted(frontier):
            for relationship in adjacency.get(node_id, ()):
                neighbor_id = neighbor_key(relationship)
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                collected.append(neighbor_id)
                next_frontier.append(neighbor_id)

        frontier = sorted(set(next_frontier))

    return tuple(sorted(collected))
