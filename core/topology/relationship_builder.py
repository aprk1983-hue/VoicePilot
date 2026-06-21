"""Deterministic relationship rules over canonical voice objects."""

from __future__ import annotations

from dataclasses import dataclass

from model.cucm_objects import (
    CallingSearchSpace,
    CUCMNode,
    DevicePool,
    Gateway,
    Partition,
    Phone,
    Region,
    RouteGroup,
    RouteList,
    RoutePattern,
    SIPTrunk,
)
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
from model.voice_graph import VoiceObject, VoiceRelationship
from model.voice_service import VoiceService
from topology.relationship_types import RelationshipType


@dataclass(frozen=True)
class _ObjectBuckets:
    dial_peers: tuple[DialPeer, ...]
    voice_services: tuple[VoiceService, ...]
    sip_uas: tuple[SipUA, ...]
    interfaces: tuple[Interface, ...]
    providers: tuple[Provider, ...]
    phones: tuple[Phone, ...] = ()
    cucm_nodes: tuple[CUCMNode, ...] = ()
    device_pools: tuple[DevicePool, ...] = ()
    regions: tuple[Region, ...] = ()
    css_objects: tuple[CallingSearchSpace, ...] = ()
    partitions: tuple[Partition, ...] = ()
    route_patterns: tuple[RoutePattern, ...] = ()
    route_lists: tuple[RouteList, ...] = ()
    route_groups: tuple[RouteGroup, ...] = ()
    gateways: tuple[Gateway, ...] = ()
    sip_trunks: tuple[SIPTrunk, ...] = ()


class RelationshipBuilder:
    """Build vendor-neutral relationships from case voice objects without guessing."""

    def build(self, voice_objects: list[VoiceObject]) -> tuple[VoiceRelationship, ...]:
        """Return deduplicated relationships implied by explicit v1 rules."""
        buckets = _partition_objects(voice_objects)
        relationships: list[VoiceRelationship] = []
        seen: set[tuple[str, str, str]] = set()

        self._add_dial_peer_uses_voice_service(buckets, relationships, seen)
        self._add_voice_service_uses_sip_ua(buckets, relationships, seen)
        self._add_sip_ua_binds_to_interface(buckets, relationships, seen)
        self._add_dial_peer_routes_to_provider(buckets, relationships, seen)
        self._add_cucm_relationships(buckets, relationships, seen)

        return tuple(relationships)

    def _add_dial_peer_uses_voice_service(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        if len(buckets.voice_services) != 1:
            return

        voice_service = buckets.voice_services[0]
        for dial_peer in buckets.dial_peers:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.USES,
                dial_peer.id,
                voice_service.id,
                description=f"{dial_peer.name} uses {voice_service.name}",
            )

    def _add_voice_service_uses_sip_ua(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        if len(buckets.voice_services) != 1 or len(buckets.sip_uas) != 1:
            return

        voice_service = buckets.voice_services[0]
        sip_ua = buckets.sip_uas[0]
        _append_relationship(
            relationships,
            seen,
            RelationshipType.USES,
            voice_service.id,
            sip_ua.id,
            description=f"{voice_service.name} uses {sip_ua.name}",
        )

    def _add_sip_ua_binds_to_interface(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        if not buckets.interfaces:
            return

        interfaces_by_hostname: dict[str, list[Interface]] = {}
        for interface in buckets.interfaces:
            interfaces_by_hostname.setdefault(interface.hostname, []).append(interface)

        for sip_ua in buckets.sip_uas:
            host_interfaces = interfaces_by_hostname.get(sip_ua.hostname, [])
            for interface in sorted(host_interfaces, key=lambda item: item.id):
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.BINDS_TO,
                    sip_ua.id,
                    interface.id,
                    description=f"{sip_ua.name} binds to {interface.name}",
                )

    def _add_dial_peer_routes_to_provider(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        if not buckets.providers:
            return

        for dial_peer in buckets.dial_peers:
            provider = _resolve_provider_for_dial_peer(dial_peer, buckets.providers)
            if provider is None:
                continue
            _append_relationship(
                relationships,
                seen,
                RelationshipType.ROUTES_TO,
                dial_peer.id,
                provider.id,
                description=f"{dial_peer.name} routes to {provider.name}",
            )


    def _add_cucm_relationships(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        phones = buckets.phones
        nodes = buckets.cucm_nodes
        device_pools = buckets.device_pools
        regions = buckets.regions
        css_list = buckets.css_objects
        partitions = buckets.partitions
        route_patterns = buckets.route_patterns
        route_lists = buckets.route_lists
        route_groups = buckets.route_groups
        gateways = buckets.gateways
        sip_trunks = buckets.sip_trunks

        node = nodes[0] if len(nodes) == 1 else None
        for phone in phones:
            if node is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.REGISTERED_TO,
                    phone.id,
                    node.id,
                    description=f"{phone.name} registered to {node.name}",
                )
            if device_pools:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    phone.id,
                    device_pools[0].id,
                    description=f"{phone.name} uses {device_pools[0].name}",
                )
            if css_list:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    phone.id,
                    css_list[0].id,
                    description=f"{phone.name} uses {css_list[0].name}",
                )

        if device_pools and regions:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.USES,
                device_pools[0].id,
                regions[0].id,
                description="Device pool uses region",
            )

        if css_list and partitions:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.USES,
                css_list[0].id,
                partitions[0].id,
                description="CSS uses partition",
            )

        if route_patterns and route_lists:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.ROUTES_TO,
                route_patterns[0].id,
                route_lists[0].id,
                description="Route pattern routes to route list",
            )

        if route_lists and route_groups:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.USES,
                route_lists[0].id,
                route_groups[0].id,
                description="Route list uses route group",
            )

        if route_groups and gateways:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.USES,
                route_groups[0].id,
                gateways[0].id,
                description="Route group uses gateway",
            )

        if gateways and sip_trunks:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.ROUTES_TO,
                gateways[0].id,
                sip_trunks[0].id,
                description="Gateway routes to SIP trunk",
            )

        if sip_trunks and buckets.providers:
            _append_relationship(
                relationships,
                seen,
                RelationshipType.ROUTES_TO,
                sip_trunks[0].id,
                buckets.providers[0].id,
                description="SIP trunk routes to provider",
            )


def _partition_objects(voice_objects: list[VoiceObject]) -> _ObjectBuckets:
    dial_peers: list[DialPeer] = []
    voice_services: list[VoiceService] = []
    sip_uas: list[SipUA] = []
    interfaces: list[Interface] = []
    providers: list[Provider] = []
    phones: list[Phone] = []
    cucm_nodes: list[CUCMNode] = []
    device_pools: list[DevicePool] = []
    regions: list[Region] = []
    css_objects: list[CallingSearchSpace] = []
    partitions: list[Partition] = []
    route_patterns: list[RoutePattern] = []
    route_lists: list[RouteList] = []
    route_groups: list[RouteGroup] = []
    gateways: list[Gateway] = []
    sip_trunks: list[SIPTrunk] = []

    for obj in voice_objects:
        if isinstance(obj, DialPeer):
            dial_peers.append(obj)
        elif isinstance(obj, VoiceService):
            voice_services.append(obj)
        elif isinstance(obj, SipUA):
            sip_uas.append(obj)
        elif isinstance(obj, Interface):
            interfaces.append(obj)
        elif isinstance(obj, Provider):
            providers.append(obj)
        elif isinstance(obj, Phone):
            phones.append(obj)
        elif isinstance(obj, CUCMNode):
            cucm_nodes.append(obj)
        elif isinstance(obj, DevicePool):
            device_pools.append(obj)
        elif isinstance(obj, Region):
            regions.append(obj)
        elif isinstance(obj, CallingSearchSpace):
            css_objects.append(obj)
        elif isinstance(obj, Partition):
            partitions.append(obj)
        elif isinstance(obj, RoutePattern):
            route_patterns.append(obj)
        elif isinstance(obj, RouteList):
            route_lists.append(obj)
        elif isinstance(obj, RouteGroup):
            route_groups.append(obj)
        elif isinstance(obj, Gateway):
            gateways.append(obj)
        elif isinstance(obj, SIPTrunk):
            sip_trunks.append(obj)

    return _ObjectBuckets(
        dial_peers=tuple(sorted(dial_peers, key=lambda item: item.id)),
        voice_services=tuple(sorted(voice_services, key=lambda item: item.id)),
        sip_uas=tuple(sorted(sip_uas, key=lambda item: item.id)),
        interfaces=tuple(sorted(interfaces, key=lambda item: item.id)),
        providers=tuple(sorted(providers, key=lambda item: item.id)),
        phones=tuple(sorted(phones, key=lambda item: item.id)),
        cucm_nodes=tuple(sorted(cucm_nodes, key=lambda item: item.id)),
        device_pools=tuple(sorted(device_pools, key=lambda item: item.id)),
        regions=tuple(sorted(regions, key=lambda item: item.id)),
        css_objects=tuple(sorted(css_objects, key=lambda item: item.id)),
        partitions=tuple(sorted(partitions, key=lambda item: item.id)),
        route_patterns=tuple(sorted(route_patterns, key=lambda item: item.id)),
        route_lists=tuple(sorted(route_lists, key=lambda item: item.id)),
        route_groups=tuple(sorted(route_groups, key=lambda item: item.id)),
        gateways=tuple(sorted(gateways, key=lambda item: item.id)),
        sip_trunks=tuple(sorted(sip_trunks, key=lambda item: item.id)),
    )


def _resolve_provider_for_dial_peer(
    dial_peer: DialPeer,
    providers: tuple[Provider, ...],
) -> Provider | None:
    if len(providers) == 1:
        return providers[0]

    session_target = (dial_peer.session_target or "").strip().lower()
    if not session_target:
        return None

    for provider in providers:
        for address in provider.addresses:
            normalized = address.strip().lower()
            if session_target == normalized or session_target in normalized:
                return provider
    return None


def _append_relationship(
    relationships: list[VoiceRelationship],
    seen: set[tuple[str, str, str]],
    relationship_type: RelationshipType,
    source_object_id: str,
    target_object_id: str,
    *,
    description: str,
) -> None:
    key = (source_object_id, target_object_id, relationship_type.value)
    if key in seen:
        return

    seen.add(key)
    relationships.append(
        VoiceRelationship.create(
            relationship_type.value,
            source_object_id,
            target_object_id,
            description=description,
        )
    )
