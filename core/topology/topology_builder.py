"""Build immutable voice topology graphs from investigation cases."""

from __future__ import annotations

from model.device import Device
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
from model.audiocodes_objects import (
    Certificate,
    EthernetInterface,
    HACluster,
    IPGroup,
    IPProfile,
    License,
    ManipulationSet,
    MediaRealm,
    MediaSecurityProfile,
    MessageManipulation,
    ProxyAddress,
    ProxySet,
    RoutingRule,
    SBCDevice,
    SIPInterface,
    SIPMessagePolicy,
    SRD,
    TLSContext,
)
from model.genesys_objects import (
    Agent,
    ArchitectFlow,
    ByocCloudTrunk,
    ByocPremisesTrunk,
    Campaign,
    DataAction,
    Division,
    EdgeDevice,
    Flow,
    GenesysOrganization,
    GenesysRegion,
    PresenceDefinition,
    Queue,
    QueueMember,
    Recording,
    RecordingPolicy,
    SipEndpoint,
    Skill,
    UserRoutingStatus,
    WrapUpCode,
)
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
            audiocodes_sbc_devices=buckets.audiocodes_sbc_devices,
            audiocodes_sip_interfaces=buckets.audiocodes_sip_interfaces,
            audiocodes_media_realms=buckets.audiocodes_media_realms,
            audiocodes_proxy_sets=buckets.audiocodes_proxy_sets,
            audiocodes_proxy_addresses=buckets.audiocodes_proxy_addresses,
            audiocodes_ip_groups=buckets.audiocodes_ip_groups,
            audiocodes_ip_profiles=buckets.audiocodes_ip_profiles,
            audiocodes_routing_rules=buckets.audiocodes_routing_rules,
            audiocodes_manipulation_sets=buckets.audiocodes_manipulation_sets,
            audiocodes_message_manipulations=buckets.audiocodes_message_manipulations,
            audiocodes_tls_contexts=buckets.audiocodes_tls_contexts,
            audiocodes_certificates=buckets.audiocodes_certificates,
            audiocodes_srds=buckets.audiocodes_srds,
            audiocodes_ethernet_interfaces=buckets.audiocodes_ethernet_interfaces,
            audiocodes_ha_clusters=buckets.audiocodes_ha_clusters,
            audiocodes_licenses=buckets.audiocodes_licenses,
            audiocodes_sip_message_policies=buckets.audiocodes_sip_message_policies,
            audiocodes_media_security_profiles=buckets.audiocodes_media_security_profiles,
            genesys_organizations=buckets.genesys_organizations,
            genesys_agents=buckets.genesys_agents,
            genesys_queues=buckets.genesys_queues,
            genesys_flows=buckets.genesys_flows,
            genesys_trunks=buckets.genesys_trunks,
            genesys_edges=buckets.genesys_edges,
            genesys_campaigns=buckets.genesys_campaigns,
            genesys_recordings=buckets.genesys_recordings,
            genesys_skills=buckets.genesys_skills,
            genesys_divisions=buckets.genesys_divisions,
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
        "audiocodes_sbc_devices",
        "audiocodes_sip_interfaces",
        "audiocodes_media_realms",
        "audiocodes_proxy_sets",
        "audiocodes_proxy_addresses",
        "audiocodes_ip_groups",
        "audiocodes_ip_profiles",
        "audiocodes_routing_rules",
        "audiocodes_manipulation_sets",
        "audiocodes_message_manipulations",
        "audiocodes_tls_contexts",
        "audiocodes_certificates",
        "audiocodes_srds",
        "audiocodes_ethernet_interfaces",
        "audiocodes_ha_clusters",
        "audiocodes_licenses",
        "audiocodes_sip_message_policies",
        "audiocodes_media_security_profiles",
        "genesys_organizations",
        "genesys_agents",
        "genesys_queues",
        "genesys_flows",
        "genesys_trunks",
        "genesys_edges",
        "genesys_campaigns",
        "genesys_recordings",
        "genesys_skills",
        "genesys_divisions",
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
        audiocodes_sbc_devices: tuple[SBCDevice, ...],
        audiocodes_sip_interfaces: tuple[SIPInterface, ...],
        audiocodes_media_realms: tuple[MediaRealm, ...],
        audiocodes_proxy_sets: tuple[ProxySet, ...],
        audiocodes_proxy_addresses: tuple[ProxyAddress, ...],
        audiocodes_ip_groups: tuple[IPGroup, ...],
        audiocodes_ip_profiles: tuple[IPProfile, ...],
        audiocodes_routing_rules: tuple[RoutingRule, ...],
        audiocodes_manipulation_sets: tuple[ManipulationSet, ...],
        audiocodes_message_manipulations: tuple[MessageManipulation, ...],
        audiocodes_tls_contexts: tuple[TLSContext, ...],
        audiocodes_certificates: tuple[Certificate, ...],
        audiocodes_srds: tuple[SRD, ...],
        audiocodes_ethernet_interfaces: tuple[EthernetInterface, ...],
        audiocodes_ha_clusters: tuple[HACluster, ...],
        audiocodes_licenses: tuple[License, ...],
        audiocodes_sip_message_policies: tuple[SIPMessagePolicy, ...],
        audiocodes_media_security_profiles: tuple[MediaSecurityProfile, ...],
        genesys_organizations: tuple[GenesysOrganization | GenesysRegion, ...],
        genesys_agents: tuple[Agent | PresenceDefinition | UserRoutingStatus, ...],
        genesys_queues: tuple[Queue | QueueMember, ...],
        genesys_flows: tuple[Flow | ArchitectFlow | DataAction | WrapUpCode, ...],
        genesys_trunks: tuple[ByocCloudTrunk | ByocPremisesTrunk | SipEndpoint, ...],
        genesys_edges: tuple[EdgeDevice, ...],
        genesys_campaigns: tuple[Campaign, ...],
        genesys_recordings: tuple[Recording | RecordingPolicy, ...],
        genesys_skills: tuple[Skill, ...],
        genesys_divisions: tuple[Division, ...],
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
        self.audiocodes_sbc_devices = audiocodes_sbc_devices
        self.audiocodes_sip_interfaces = audiocodes_sip_interfaces
        self.audiocodes_media_realms = audiocodes_media_realms
        self.audiocodes_proxy_sets = audiocodes_proxy_sets
        self.audiocodes_proxy_addresses = audiocodes_proxy_addresses
        self.audiocodes_ip_groups = audiocodes_ip_groups
        self.audiocodes_ip_profiles = audiocodes_ip_profiles
        self.audiocodes_routing_rules = audiocodes_routing_rules
        self.audiocodes_manipulation_sets = audiocodes_manipulation_sets
        self.audiocodes_message_manipulations = audiocodes_message_manipulations
        self.audiocodes_tls_contexts = audiocodes_tls_contexts
        self.audiocodes_certificates = audiocodes_certificates
        self.audiocodes_srds = audiocodes_srds
        self.audiocodes_ethernet_interfaces = audiocodes_ethernet_interfaces
        self.audiocodes_ha_clusters = audiocodes_ha_clusters
        self.audiocodes_licenses = audiocodes_licenses
        self.audiocodes_sip_message_policies = audiocodes_sip_message_policies
        self.audiocodes_media_security_profiles = audiocodes_media_security_profiles
        self.genesys_organizations = genesys_organizations
        self.genesys_agents = genesys_agents
        self.genesys_queues = genesys_queues
        self.genesys_flows = genesys_flows
        self.genesys_trunks = genesys_trunks
        self.genesys_edges = genesys_edges
        self.genesys_campaigns = genesys_campaigns
        self.genesys_recordings = genesys_recordings
        self.genesys_skills = genesys_skills
        self.genesys_divisions = genesys_divisions


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
    audiocodes_sbc_devices: list[SBCDevice] = []
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
    audiocodes_srds: list[SRD] = []
    audiocodes_ethernet_interfaces: list[EthernetInterface] = []
    audiocodes_ha_clusters: list[HACluster] = []
    audiocodes_licenses: list[License] = []
    audiocodes_sip_message_policies: list[SIPMessagePolicy] = []
    audiocodes_media_security_profiles: list[MediaSecurityProfile] = []
    genesys_organizations: list[GenesysOrganization | GenesysRegion] = []
    genesys_agents: list[Agent | PresenceDefinition | UserRoutingStatus] = []
    genesys_queues: list[Queue | QueueMember] = []
    genesys_flows: list[Flow | ArchitectFlow | DataAction | WrapUpCode] = []
    genesys_trunks: list[ByocCloudTrunk | ByocPremisesTrunk | SipEndpoint] = []
    genesys_edges: list[EdgeDevice] = []
    genesys_campaigns: list[Campaign] = []
    genesys_recordings: list[Recording | RecordingPolicy] = []
    genesys_skills: list[Skill] = []
    genesys_divisions: list[Division] = []

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
        elif isinstance(obj, SBCDevice):
            audiocodes_sbc_devices.append(obj)
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
        elif isinstance(obj, SRD):
            audiocodes_srds.append(obj)
        elif isinstance(obj, EthernetInterface):
            audiocodes_ethernet_interfaces.append(obj)
        elif isinstance(obj, HACluster):
            audiocodes_ha_clusters.append(obj)
        elif isinstance(obj, License):
            audiocodes_licenses.append(obj)
        elif isinstance(obj, SIPMessagePolicy):
            audiocodes_sip_message_policies.append(obj)
        elif isinstance(obj, MediaSecurityProfile):
            audiocodes_media_security_profiles.append(obj)
        elif isinstance(obj, (GenesysOrganization, GenesysRegion)):
            genesys_organizations.append(obj)
        elif isinstance(obj, (Agent, PresenceDefinition, UserRoutingStatus)):
            genesys_agents.append(obj)
        elif isinstance(obj, (Queue, QueueMember)):
            genesys_queues.append(obj)
        elif isinstance(obj, (Flow, ArchitectFlow, DataAction, WrapUpCode)):
            genesys_flows.append(obj)
        elif isinstance(obj, (ByocCloudTrunk, ByocPremisesTrunk, SipEndpoint)):
            genesys_trunks.append(obj)
        elif isinstance(obj, EdgeDevice):
            genesys_edges.append(obj)
        elif isinstance(obj, Campaign):
            genesys_campaigns.append(obj)
        elif isinstance(obj, (Recording, RecordingPolicy)):
            genesys_recordings.append(obj)
        elif isinstance(obj, Skill):
            genesys_skills.append(obj)
        elif isinstance(obj, Division):
            genesys_divisions.append(obj)

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
        audiocodes_sbc_devices=tuple(sorted(audiocodes_sbc_devices, key=lambda item: item.id)),
        audiocodes_sip_interfaces=tuple(sorted(audiocodes_sip_interfaces, key=lambda item: item.id)),
        audiocodes_media_realms=tuple(sorted(audiocodes_media_realms, key=lambda item: item.id)),
        audiocodes_proxy_sets=tuple(sorted(audiocodes_proxy_sets, key=lambda item: item.id)),
        audiocodes_proxy_addresses=tuple(sorted(audiocodes_proxy_addresses, key=lambda item: item.id)),
        audiocodes_ip_groups=tuple(sorted(audiocodes_ip_groups, key=lambda item: item.id)),
        audiocodes_ip_profiles=tuple(sorted(audiocodes_ip_profiles, key=lambda item: item.id)),
        audiocodes_routing_rules=tuple(sorted(audiocodes_routing_rules, key=lambda item: item.id)),
        audiocodes_manipulation_sets=tuple(sorted(audiocodes_manipulation_sets, key=lambda item: item.id)),
        audiocodes_message_manipulations=tuple(
            sorted(audiocodes_message_manipulations, key=lambda item: item.id)
        ),
        audiocodes_tls_contexts=tuple(sorted(audiocodes_tls_contexts, key=lambda item: item.id)),
        audiocodes_certificates=tuple(sorted(audiocodes_certificates, key=lambda item: item.id)),
        audiocodes_srds=tuple(sorted(audiocodes_srds, key=lambda item: item.id)),
        audiocodes_ethernet_interfaces=tuple(
            sorted(audiocodes_ethernet_interfaces, key=lambda item: item.id)
        ),
        audiocodes_ha_clusters=tuple(sorted(audiocodes_ha_clusters, key=lambda item: item.id)),
        audiocodes_licenses=tuple(sorted(audiocodes_licenses, key=lambda item: item.id)),
        audiocodes_sip_message_policies=tuple(
            sorted(audiocodes_sip_message_policies, key=lambda item: item.id)
        ),
        audiocodes_media_security_profiles=tuple(
            sorted(audiocodes_media_security_profiles, key=lambda item: item.id)
        ),
        genesys_organizations=tuple(sorted(genesys_organizations, key=lambda item: item.id)),
        genesys_agents=tuple(sorted(genesys_agents, key=lambda item: item.id)),
        genesys_queues=tuple(sorted(genesys_queues, key=lambda item: item.id)),
        genesys_flows=tuple(sorted(genesys_flows, key=lambda item: item.id)),
        genesys_trunks=tuple(sorted(genesys_trunks, key=lambda item: item.id)),
        genesys_edges=tuple(sorted(genesys_edges, key=lambda item: item.id)),
        genesys_campaigns=tuple(sorted(genesys_campaigns, key=lambda item: item.id)),
        genesys_recordings=tuple(sorted(genesys_recordings, key=lambda item: item.id)),
        genesys_skills=tuple(sorted(genesys_skills, key=lambda item: item.id)),
        genesys_divisions=tuple(sorted(genesys_divisions, key=lambda item: item.id)),
    )
