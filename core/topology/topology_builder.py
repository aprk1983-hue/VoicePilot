"""Build immutable voice topology graphs from investigation cases."""

from __future__ import annotations

from model.device import Device
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
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
from model.voice_graph import VoiceObject
from model.voice_service import VoiceService
from model.voice_topology import VoiceTopology
from topology.relationship_builder import RelationshipBuilder


class TopologyBuilder:
    """Assemble a ``VoiceTopology`` from canonical case voice objects."""

    def __init__(self, relationship_builder: RelationshipBuilder | None = None) -> None:
        self._relationship_builder = relationship_builder or RelationshipBuilder()

    def build(self, voice_objects: list[VoiceObject]) -> VoiceTopology:
        """Create an immutable topology containing all objects and inferred relationships."""
        buckets = _partition_all_objects(voice_objects)
        relationships = self._relationship_builder.build(voice_objects)
        return VoiceTopology(
            devices=buckets.devices,
            interfaces=buckets.interfaces,
            voice_services=buckets.voice_services,
            sip_uas=buckets.sip_uas,
            providers=buckets.providers,
            dial_peers=buckets.dial_peers,
            teams_users=buckets.teams_users,
            teams_phone_numbers=buckets.teams_phone_numbers,
            teams_voice_routing_policies=buckets.teams_voice_routing_policies,
            teams_voice_routes=buckets.teams_voice_routes,
            teams_dial_plans=buckets.teams_dial_plans,
            teams_pstn_gateways=buckets.teams_pstn_gateways,
            teams_pstn_usages=buckets.teams_pstn_usages,
            teams_call_queues=buckets.teams_call_queues,
            teams_auto_attendants=buckets.teams_auto_attendants,
            teams_resource_accounts=buckets.teams_resource_accounts,
            teams_lis_locations=buckets.teams_lis_locations,
            relationships=relationships,
        )


class _TopologyBuckets:
    __slots__ = (
        "devices",
        "interfaces",
        "voice_services",
        "sip_uas",
        "providers",
        "dial_peers",
        "teams_users",
        "teams_phone_numbers",
        "teams_voice_routing_policies",
        "teams_voice_routes",
        "teams_dial_plans",
        "teams_pstn_gateways",
        "teams_pstn_usages",
        "teams_call_queues",
        "teams_auto_attendants",
        "teams_resource_accounts",
        "teams_lis_locations",
    )

    def __init__(
        self,
        *,
        devices: tuple[Device, ...],
        interfaces: tuple[Interface, ...],
        voice_services: tuple[VoiceService, ...],
        sip_uas: tuple[SipUA, ...],
        providers: tuple[Provider, ...],
        dial_peers: tuple[DialPeer, ...],
        teams_users: tuple[TeamsUser, ...],
        teams_phone_numbers: tuple[TeamsPhoneNumber, ...],
        teams_voice_routing_policies: tuple[TeamsVoiceRoutingPolicy, ...],
        teams_voice_routes: tuple[TeamsVoiceRoute, ...],
        teams_dial_plans: tuple[TeamsDialPlan, ...],
        teams_pstn_gateways: tuple[TeamsPstnGateway, ...],
        teams_pstn_usages: tuple[TeamsPstnUsage, ...],
        teams_call_queues: tuple[TeamsCallQueue, ...],
        teams_auto_attendants: tuple[TeamsAutoAttendant, ...],
        teams_resource_accounts: tuple[TeamsResourceAccount, ...],
        teams_lis_locations: tuple[TeamsLisLocation, ...],
    ) -> None:
        self.devices = devices
        self.interfaces = interfaces
        self.voice_services = voice_services
        self.sip_uas = sip_uas
        self.providers = providers
        self.dial_peers = dial_peers
        self.teams_users = teams_users
        self.teams_phone_numbers = teams_phone_numbers
        self.teams_voice_routing_policies = teams_voice_routing_policies
        self.teams_voice_routes = teams_voice_routes
        self.teams_dial_plans = teams_dial_plans
        self.teams_pstn_gateways = teams_pstn_gateways
        self.teams_pstn_usages = teams_pstn_usages
        self.teams_call_queues = teams_call_queues
        self.teams_auto_attendants = teams_auto_attendants
        self.teams_resource_accounts = teams_resource_accounts
        self.teams_lis_locations = teams_lis_locations


def _partition_all_objects(voice_objects: list[VoiceObject]) -> _TopologyBuckets:
    devices: list[Device] = []
    interfaces: list[Interface] = []
    voice_services: list[VoiceService] = []
    sip_uas: list[SipUA] = []
    providers: list[Provider] = []
    dial_peers: list[DialPeer] = []
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

    for obj in voice_objects:
        if isinstance(obj, Device):
            devices.append(obj)
        elif isinstance(obj, Interface):
            interfaces.append(obj)
        elif isinstance(obj, VoiceService):
            voice_services.append(obj)
        elif isinstance(obj, SipUA):
            sip_uas.append(obj)
        elif isinstance(obj, Provider):
            providers.append(obj)
        elif isinstance(obj, DialPeer):
            dial_peers.append(obj)
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

    return _TopologyBuckets(
        devices=tuple(sorted(devices, key=lambda item: item.id)),
        interfaces=tuple(sorted(interfaces, key=lambda item: item.id)),
        voice_services=tuple(sorted(voice_services, key=lambda item: item.id)),
        sip_uas=tuple(sorted(sip_uas, key=lambda item: item.id)),
        providers=tuple(sorted(providers, key=lambda item: item.id)),
        dial_peers=tuple(sorted(dial_peers, key=lambda item: item.id)),
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
    )
