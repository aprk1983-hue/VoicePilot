"""Canonical Voice Object Model (CVOM) — vendor-neutral voice deployment objects."""

from model.codec_class import CodecClass
from model.device import Device
from model.dial_peer import DialPeer
from model.interface import Interface
from model.object_registry import ObjectRegistry
from model.provider import Provider
from model.server_group import ServerGroup
from model.sip_ua import SipUA
from model.translation_profile import TranslationProfile
from model.translation_rule import TranslationRule
from model.voice_graph import VoiceObject, VoiceRelationship
from model.voice_service import VoiceService
from model.voice_topology import VoiceTopology

__all__ = [
    "CodecClass",
    "Device",
    "DialPeer",
    "Interface",
    "ObjectRegistry",
    "Provider",
    "ServerGroup",
    "SipUA",
    "TranslationProfile",
    "TranslationRule",
    "VoiceObject",
    "VoiceRelationship",
    "VoiceService",
    "VoiceTopology",
]
