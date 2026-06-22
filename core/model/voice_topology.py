"""Canonical voice topology container."""

from __future__ import annotations

from dataclasses import dataclass, field

from model.device import Device
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


@dataclass(frozen=True)
class VoiceTopology:
    """Collection of canonical voice objects and their relationships.

  v1 is a typed container only — no graph algorithms or path building.
    """

    devices: tuple[Device, ...] = field(default_factory=tuple)
    interfaces: tuple[Interface, ...] = field(default_factory=tuple)
    voice_services: tuple[VoiceService, ...] = field(default_factory=tuple)
    sip_uas: tuple[SipUA, ...] = field(default_factory=tuple)
    providers: tuple[Provider, ...] = field(default_factory=tuple)
    dial_peers: tuple[DialPeer, ...] = field(default_factory=tuple)
    teams_users: tuple[TeamsUser, ...] = field(default_factory=tuple)
    teams_phone_numbers: tuple[TeamsPhoneNumber, ...] = field(default_factory=tuple)
    teams_voice_routing_policies: tuple[TeamsVoiceRoutingPolicy, ...] = field(default_factory=tuple)
    teams_voice_routes: tuple[TeamsVoiceRoute, ...] = field(default_factory=tuple)
    teams_dial_plans: tuple[TeamsDialPlan, ...] = field(default_factory=tuple)
    teams_pstn_gateways: tuple[TeamsPstnGateway, ...] = field(default_factory=tuple)
    teams_pstn_usages: tuple[TeamsPstnUsage, ...] = field(default_factory=tuple)
    teams_call_queues: tuple[TeamsCallQueue, ...] = field(default_factory=tuple)
    teams_auto_attendants: tuple[TeamsAutoAttendant, ...] = field(default_factory=tuple)
    teams_resource_accounts: tuple[TeamsResourceAccount, ...] = field(default_factory=tuple)
    teams_lis_locations: tuple[TeamsLisLocation, ...] = field(default_factory=tuple)
    relationships: tuple[VoiceRelationship, ...] = field(default_factory=tuple)

    @property
    def object_count(self) -> int:
        return (
            len(self.devices)
            + len(self.interfaces)
            + len(self.voice_services)
            + len(self.sip_uas)
            + len(self.providers)
            + len(self.dial_peers)
            + len(self.teams_users)
            + len(self.teams_phone_numbers)
            + len(self.teams_voice_routing_policies)
            + len(self.teams_voice_routes)
            + len(self.teams_dial_plans)
            + len(self.teams_pstn_gateways)
            + len(self.teams_pstn_usages)
            + len(self.teams_call_queues)
            + len(self.teams_auto_attendants)
            + len(self.teams_resource_accounts)
            + len(self.teams_lis_locations)
        )

    def all_objects(
        self,
    ) -> tuple[VoiceObject, ...]:
        """Return all contained voice objects in stable order."""
        return (
            *self.devices,
            *self.interfaces,
            *self.voice_services,
            *self.sip_uas,
            *self.providers,
            *self.dial_peers,
            *self.teams_users,
            *self.teams_phone_numbers,
            *self.teams_voice_routing_policies,
            *self.teams_voice_routes,
            *self.teams_dial_plans,
            *self.teams_pstn_gateways,
            *self.teams_pstn_usages,
            *self.teams_call_queues,
            *self.teams_auto_attendants,
            *self.teams_resource_accounts,
            *self.teams_lis_locations,
        )
