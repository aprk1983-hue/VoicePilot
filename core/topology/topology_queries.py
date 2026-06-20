"""High-level topology query helpers built on dependency traversal."""

from __future__ import annotations

from model.dial_peer import DialPeer
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology
from topology.dependency_engine import DependencyEngine
from topology.relationship_types import RelationshipType
from topology.topology_exceptions import TopologyObjectNotFoundError


class TopologyQueries:
    """Convenience queries over canonical voice topology graphs."""

    def __init__(self, dependency_engine: DependencyEngine | None = None) -> None:
        self._dependency_engine = dependency_engine or DependencyEngine()

    def find_dial_peers_using_voice_service(self, topology: VoiceTopology) -> tuple[DialPeer, ...]:
        """Return dial peers with a ``uses`` relationship to any voice service."""
        voice_service_ids = {voice_service.id for voice_service in topology.voice_services}
        if not voice_service_ids:
            return ()

        dial_peer_ids = sorted(
            {
                relationship.source_object_id
                for relationship in topology.relationships
                if (
                    relationship.relationship_type == RelationshipType.USES.value
                    and relationship.target_object_id in voice_service_ids
                )
            }
        )
        dial_peers_by_id = {dial_peer.id: dial_peer for dial_peer in topology.dial_peers}
        return tuple(dial_peers_by_id[dial_peer_id] for dial_peer_id in dial_peer_ids)

    def find_dial_peers_routing_to_provider(
        self,
        topology: VoiceTopology,
        provider_id: str,
    ) -> tuple[DialPeer, ...]:
        """Return dial peers with a ``routes_to`` relationship to ``provider_id``."""
        if provider_id not in {provider.id for provider in topology.providers}:
            raise TopologyObjectNotFoundError(provider_id)

        dial_peer_ids = sorted(
            {
                relationship.source_object_id
                for relationship in topology.relationships
                if (
                    relationship.relationship_type == RelationshipType.ROUTES_TO.value
                    and relationship.target_object_id == provider_id
                )
            }
        )
        dial_peers_by_id = {dial_peer.id: dial_peer for dial_peer in topology.dial_peers}
        return tuple(dial_peers_by_id[dial_peer_id] for dial_peer_id in dial_peer_ids)

    def find_objects_depending_on_sipua(self, topology: VoiceTopology) -> tuple[VoiceObject, ...]:
        """Return all objects that transitively depend on any SIP-UA in the topology."""
        if not topology.sip_uas:
            return ()

        object_index = {obj.id: obj for obj in topology.all_objects()}
        dependent_ids: set[str] = set()
        for sip_ua in topology.sip_uas:
            dependent_ids.update(
                self._dependency_engine.get_transitive_dependents(topology, sip_ua.id)
            )

        return tuple(object_index[object_id] for object_id in sorted(dependent_ids))
