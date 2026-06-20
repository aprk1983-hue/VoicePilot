"""Deterministic relationship rules over canonical voice objects."""

from __future__ import annotations

from dataclasses import dataclass

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


def _partition_objects(voice_objects: list[VoiceObject]) -> _ObjectBuckets:
    dial_peers: list[DialPeer] = []
    voice_services: list[VoiceService] = []
    sip_uas: list[SipUA] = []
    interfaces: list[Interface] = []
    providers: list[Provider] = []

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

    return _ObjectBuckets(
        dial_peers=tuple(sorted(dial_peers, key=lambda item: item.id)),
        voice_services=tuple(sorted(voice_services, key=lambda item: item.id)),
        sip_uas=tuple(sorted(sip_uas, key=lambda item: item.id)),
        interfaces=tuple(sorted(interfaces, key=lambda item: item.id)),
        providers=tuple(sorted(providers, key=lambda item: item.id)),
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
