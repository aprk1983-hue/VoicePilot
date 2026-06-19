"""Canonical voice topology container."""

from __future__ import annotations

from dataclasses import dataclass, field

from model.device import Device
from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.voice_graph import VoiceRelationship


@dataclass(frozen=True)
class VoiceTopology:
    """Collection of canonical voice objects and their relationships.

  v1 is a typed container only — no graph algorithms or path building.
    """

    devices: tuple[Device, ...] = field(default_factory=tuple)
    interfaces: tuple[Interface, ...] = field(default_factory=tuple)
    providers: tuple[Provider, ...] = field(default_factory=tuple)
    dial_peers: tuple[DialPeer, ...] = field(default_factory=tuple)
    relationships: tuple[VoiceRelationship, ...] = field(default_factory=tuple)

    @property
    def object_count(self) -> int:
        return (
            len(self.devices)
            + len(self.interfaces)
            + len(self.providers)
            + len(self.dial_peers)
        )

    def all_objects(self) -> tuple[Device | Interface | Provider | DialPeer, ...]:
        """Return all contained voice objects in stable order."""
        return (*self.devices, *self.interfaces, *self.providers, *self.dial_peers)
