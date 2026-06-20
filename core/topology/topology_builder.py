"""Build immutable voice topology graphs from investigation cases."""

from __future__ import annotations

from model.device import Device
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
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
    ) -> None:
        self.devices = devices
        self.interfaces = interfaces
        self.voice_services = voice_services
        self.sip_uas = sip_uas
        self.providers = providers
        self.dial_peers = dial_peers


def _partition_all_objects(voice_objects: list[VoiceObject]) -> _TopologyBuckets:
    devices: list[Device] = []
    interfaces: list[Interface] = []
    voice_services: list[VoiceService] = []
    sip_uas: list[SipUA] = []
    providers: list[Provider] = []
    dial_peers: list[DialPeer] = []

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

    return _TopologyBuckets(
        devices=tuple(sorted(devices, key=lambda item: item.id)),
        interfaces=tuple(sorted(interfaces, key=lambda item: item.id)),
        voice_services=tuple(sorted(voice_services, key=lambda item: item.id)),
        sip_uas=tuple(sorted(sip_uas, key=lambda item: item.id)),
        providers=tuple(sorted(providers, key=lambda item: item.id)),
        dial_peers=tuple(sorted(dial_peers, key=lambda item: item.id)),
    )
