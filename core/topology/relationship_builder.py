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
from model.audiocodes_objects import (
    Certificate,
    IPGroup,
    IPProfile,
    ManipulationSet,
    MediaRealm,
    MessageManipulation,
    ProxyAddress,
    ProxySet,
    RoutingRule,
    SIPInterface,
    TLSContext,
)
from model.audiocodes_objects import (
    Certificate,
    IPGroup,
    IPProfile,
    ManipulationSet,
    MediaRealm,
    MessageManipulation,
    ProxyAddress,
    ProxySet,
    RoutingRule,
    SIPInterface,
    TLSContext,
)
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
from model.voice_graph import VoiceObject, VoiceRelationship
from model.voice_service import VoiceService
from model.teams_objects import (
    TeamsAutoAttendant,
    TeamsCallQueue,
    TeamsDialPlan,
    TeamsLisLocation,
    TeamsPhoneNumber,
    TeamsPstnGateway,
    TeamsPstnUsage,
    TeamsResourceAccount,
    TeamsUser,
    TeamsVoiceRoute,
    TeamsVoiceRoutingPolicy,
)
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
    teams_users: tuple[TeamsUser, ...] = ()
    teams_phone_numbers: tuple[TeamsPhoneNumber, ...] = ()
    teams_voice_routing_policies: tuple[TeamsVoiceRoutingPolicy, ...] = ()
    teams_voice_routes: tuple[TeamsVoiceRoute, ...] = ()
    teams_dial_plans: tuple[TeamsDialPlan, ...] = ()
    teams_pstn_gateways: tuple[TeamsPstnGateway, ...] = ()
    teams_pstn_usages: tuple[TeamsPstnUsage, ...] = ()
    teams_call_queues: tuple[TeamsCallQueue, ...] = ()
    teams_auto_attendants: tuple[TeamsAutoAttendant, ...] = ()
    teams_resource_accounts: tuple[TeamsResourceAccount, ...] = ()
    teams_lis_locations: tuple[TeamsLisLocation, ...] = ()
    audiocodes_sip_interfaces: tuple[SIPInterface, ...] = ()
    audiocodes_media_realms: tuple[MediaRealm, ...] = ()
    audiocodes_proxy_sets: tuple[ProxySet, ...] = ()
    audiocodes_proxy_addresses: tuple[ProxyAddress, ...] = ()
    audiocodes_ip_groups: tuple[IPGroup, ...] = ()
    audiocodes_ip_profiles: tuple[IPProfile, ...] = ()
    audiocodes_routing_rules: tuple[RoutingRule, ...] = ()
    audiocodes_manipulation_sets: tuple[ManipulationSet, ...] = ()
    audiocodes_message_manipulations: tuple[MessageManipulation, ...] = ()
    audiocodes_tls_contexts: tuple[TLSContext, ...] = ()
    audiocodes_certificates: tuple[Certificate, ...] = ()


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
        self._add_teams_relationships(buckets, relationships, seen)
        self._add_audiocodes_relationships(buckets, relationships, seen)

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

    def _add_teams_relationships(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        policy_by_name = {policy.name: policy for policy in buckets.teams_voice_routing_policies}
        usage_by_name = {usage.name: usage for usage in buckets.teams_pstn_usages}
        gateway_by_name = {gateway.name: gateway for gateway in buckets.teams_pstn_gateways}
        resource_by_name = {
            account.name: account for account in buckets.teams_resource_accounts
        }

        for user in buckets.teams_users:
            policy_name = user.voice_routing_policy
            if policy_name and policy_name in policy_by_name:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    user.id,
                    policy_by_name[policy_name].id,
                    description=f"{user.name} uses voice routing policy {policy_name}",
                )

        for route in buckets.teams_voice_routes:
            for usage_name in route.online_pstn_usages:
                usage = usage_by_name.get(usage_name)
                if usage is not None:
                    _append_relationship(
                        relationships,
                        seen,
                        RelationshipType.USES,
                        route.id,
                        usage.id,
                        description=f"{route.name} uses PSTN usage {usage_name}",
                    )
            for gateway_name in route.online_pstn_gateway_list:
                gateway = gateway_by_name.get(gateway_name)
                if gateway is not None:
                    _append_relationship(
                        relationships,
                        seen,
                        RelationshipType.ROUTES_TO,
                        route.id,
                        gateway.id,
                        description=f"{route.name} routes to gateway {gateway_name}",
                    )

        for queue in buckets.teams_call_queues:
            for resource_name in resource_by_name:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    queue.id,
                    resource_by_name[resource_name].id,
                    description=f"{queue.name} uses resource account {resource_name}",
                )
                break

        for attendant in buckets.teams_auto_attendants:
            for resource_name in resource_by_name:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    attendant.id,
                    resource_by_name[resource_name].id,
                    description=f"{attendant.name} uses resource account {resource_name}",
                )
                break

    def _add_audiocodes_relationships(
        self,
        buckets: _ObjectBuckets,
        relationships: list[VoiceRelationship],
        seen: set[tuple[str, str, str]],
    ) -> None:
        proxy_set_by_name = {item.name: item for item in buckets.audiocodes_proxy_sets}
        media_realm_by_name = {item.name: item for item in buckets.audiocodes_media_realms}
        ip_profile_by_name = {item.name: item for item in buckets.audiocodes_ip_profiles}
        ip_group_by_name = {item.name: item for item in buckets.audiocodes_ip_groups}
        tls_context_by_name = {item.name: item for item in buckets.audiocodes_tls_contexts}
        certificate_by_name = {item.name: item for item in buckets.audiocodes_certificates}
        manipulation_set_by_name = {item.name: item for item in buckets.audiocodes_manipulation_sets}

        for ip_group in buckets.audiocodes_ip_groups:
            proxy_set = proxy_set_by_name.get(ip_group.proxy_set or "")
            if proxy_set is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    ip_group.id,
                    proxy_set.id,
                    description=f"{ip_group.name} uses proxy set {ip_group.proxy_set}",
                )
            media_realm = media_realm_by_name.get(ip_group.media_realm or "")
            if media_realm is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    ip_group.id,
                    media_realm.id,
                    description=f"{ip_group.name} uses media realm {ip_group.media_realm}",
                )
            ip_profile = ip_profile_by_name.get(ip_group.ip_profile or "")
            if ip_profile is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    ip_group.id,
                    ip_profile.id,
                    description=f"{ip_group.name} uses IP profile {ip_group.ip_profile}",
                )

        for rule in buckets.audiocodes_routing_rules:
            ip_group = ip_group_by_name.get(rule.ip_group or "")
            if ip_group is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.ROUTES_TO,
                    rule.id,
                    ip_group.id,
                    description=f"{rule.name} routes to IP group {rule.ip_group}",
                )

        for address in buckets.audiocodes_proxy_addresses:
            proxy_set = proxy_set_by_name.get(address.proxy_set_name or "")
            if proxy_set is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    proxy_set.id,
                    address.id,
                    description=f"{proxy_set.name} uses proxy address {address.name}",
                )

        for sip_interface in buckets.audiocodes_sip_interfaces:
            tls_context = tls_context_by_name.get(sip_interface.tls_context or "")
            if tls_context is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    sip_interface.id,
                    tls_context.id,
                    description=f"{sip_interface.name} uses TLS context {sip_interface.tls_context}",
                )
            media_realm = media_realm_by_name.get(sip_interface.media_realm or "")
            if media_realm is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    sip_interface.id,
                    media_realm.id,
                    description=f"{sip_interface.name} uses media realm {sip_interface.media_realm}",
                )

        for tls_context in buckets.audiocodes_tls_contexts:
            certificate = certificate_by_name.get(tls_context.certificate_name or "")
            if certificate is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    tls_context.id,
                    certificate.id,
                    description=f"{tls_context.name} uses certificate {tls_context.certificate_name}",
                )

        for manipulation in buckets.audiocodes_message_manipulations:
            manipulation_set = manipulation_set_by_name.get(manipulation.set_name or "")
            if manipulation_set is not None:
                _append_relationship(
                    relationships,
                    seen,
                    RelationshipType.USES,
                    manipulation_set.id,
                    manipulation.id,
                    description=f"{manipulation_set.name} uses message manipulation {manipulation.name}",
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
    teams_users: list[TeamsUser] = []
    teams_phone_numbers: list[TeamsPhoneNumber] = []
    teams_voice_routing_policies: list[TeamsVoiceRoutingPolicy] = []
    teams_voice_routes: list[TeamsVoiceRoute] = []
    teams_dial_plans: list[TeamsDialPlan] = []
    teams_pstn_gateways: list[TeamsPstnGateway] = []
    teams_pstn_usages: list[TeamsPstnUsage] = []
    teams_call_queues: list[TeamsCallQueue] = []
    teams_auto_attendants: list[TeamsAutoAttendant] = []
    teams_resource_accounts: list[TeamsResourceAccount] = []
    teams_lis_locations: list[TeamsLisLocation] = []
    audiocodes_sip_interfaces: list[SIPInterface] = []
    audiocodes_media_realms: list[MediaRealm] = []
    audiocodes_proxy_sets: list[ProxySet] = []
    audiocodes_proxy_addresses: list[ProxyAddress] = []
    audiocodes_ip_groups: list[IPGroup] = []
    audiocodes_ip_profiles: list[IPProfile] = []
    audiocodes_routing_rules: list[RoutingRule] = []
    audiocodes_manipulation_sets: list[ManipulationSet] = []
    audiocodes_message_manipulations: list[MessageManipulation] = []
    audiocodes_tls_contexts: list[TLSContext] = []
    audiocodes_certificates: list[Certificate] = []

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
        elif isinstance(obj, TeamsUser):
            teams_users.append(obj)
        elif isinstance(obj, TeamsPhoneNumber):
            teams_phone_numbers.append(obj)
        elif isinstance(obj, TeamsVoiceRoutingPolicy):
            teams_voice_routing_policies.append(obj)
        elif isinstance(obj, TeamsVoiceRoute):
            teams_voice_routes.append(obj)
        elif isinstance(obj, TeamsDialPlan):
            teams_dial_plans.append(obj)
        elif isinstance(obj, TeamsPstnGateway):
            teams_pstn_gateways.append(obj)
        elif isinstance(obj, TeamsPstnUsage):
            teams_pstn_usages.append(obj)
        elif isinstance(obj, TeamsCallQueue):
            teams_call_queues.append(obj)
        elif isinstance(obj, TeamsAutoAttendant):
            teams_auto_attendants.append(obj)
        elif isinstance(obj, TeamsResourceAccount):
            teams_resource_accounts.append(obj)
        elif isinstance(obj, TeamsLisLocation):
            teams_lis_locations.append(obj)
        elif isinstance(obj, SIPInterface):
            audiocodes_sip_interfaces.append(obj)
        elif isinstance(obj, MediaRealm):
            audiocodes_media_realms.append(obj)
        elif isinstance(obj, ProxySet):
            audiocodes_proxy_sets.append(obj)
        elif isinstance(obj, ProxyAddress):
            audiocodes_proxy_addresses.append(obj)
        elif isinstance(obj, IPGroup):
            audiocodes_ip_groups.append(obj)
        elif isinstance(obj, IPProfile):
            audiocodes_ip_profiles.append(obj)
        elif isinstance(obj, RoutingRule):
            audiocodes_routing_rules.append(obj)
        elif isinstance(obj, ManipulationSet):
            audiocodes_manipulation_sets.append(obj)
        elif isinstance(obj, MessageManipulation):
            audiocodes_message_manipulations.append(obj)
        elif isinstance(obj, TLSContext):
            audiocodes_tls_contexts.append(obj)
        elif isinstance(obj, Certificate):
            audiocodes_certificates.append(obj)

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
        teams_users=tuple(sorted(teams_users, key=lambda item: item.id)),
        teams_phone_numbers=tuple(sorted(teams_phone_numbers, key=lambda item: item.id)),
        teams_voice_routing_policies=tuple(
            sorted(teams_voice_routing_policies, key=lambda item: item.id)
        ),
        teams_voice_routes=tuple(sorted(teams_voice_routes, key=lambda item: item.id)),
        teams_dial_plans=tuple(sorted(teams_dial_plans, key=lambda item: item.id)),
        teams_pstn_gateways=tuple(sorted(teams_pstn_gateways, key=lambda item: item.id)),
        teams_pstn_usages=tuple(sorted(teams_pstn_usages, key=lambda item: item.id)),
        teams_call_queues=tuple(sorted(teams_call_queues, key=lambda item: item.id)),
        teams_auto_attendants=tuple(sorted(teams_auto_attendants, key=lambda item: item.id)),
        teams_resource_accounts=tuple(sorted(teams_resource_accounts, key=lambda item: item.id)),
        teams_lis_locations=tuple(sorted(teams_lis_locations, key=lambda item: item.id)),
        audiocodes_sip_interfaces=tuple(sorted(audiocodes_sip_interfaces, key=lambda item: item.id)),
        audiocodes_media_realms=tuple(sorted(audiocodes_media_realms, key=lambda item: item.id)),
        audiocodes_proxy_sets=tuple(sorted(audiocodes_proxy_sets, key=lambda item: item.id)),
        audiocodes_proxy_addresses=tuple(sorted(audiocodes_proxy_addresses, key=lambda item: item.id)),
        audiocodes_ip_groups=tuple(sorted(audiocodes_ip_groups, key=lambda item: item.id)),
        audiocodes_ip_profiles=tuple(sorted(audiocodes_ip_profiles, key=lambda item: item.id)),
        audiocodes_routing_rules=tuple(sorted(audiocodes_routing_rules, key=lambda item: item.id)),
        audiocodes_manipulation_sets=tuple(
            sorted(audiocodes_manipulation_sets, key=lambda item: item.id)
        ),
        audiocodes_message_manipulations=tuple(
            sorted(audiocodes_message_manipulations, key=lambda item: item.id)
        ),
        audiocodes_tls_contexts=tuple(sorted(audiocodes_tls_contexts, key=lambda item: item.id)),
        audiocodes_certificates=tuple(sorted(audiocodes_certificates, key=lambda item: item.id)),
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
