"""Cisco parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.cisco.parser.debug_ccsip_messages import CiscoDebugCcsipMessagesParser
from plugins.cisco.parser.show_dial_peer_voice_summary import CiscoShowDialPeerVoiceSummaryParser
from plugins.cisco.parser.show_run_voice_service_voip import CiscoShowRunVoiceServiceVoipParser
from plugins.cisco.parser.show_sip_ua_status import CiscoShowSipUaStatusParser


def register_cisco_parsers(registry: ParserRegistry) -> None:
    """Register all Cisco command parsers with the given registry."""
    registry.register(CiscoShowSipUaStatusParser())
    registry.register(CiscoDebugCcsipMessagesParser())
    registry.register(CiscoShowDialPeerVoiceSummaryParser())
    registry.register(CiscoShowRunVoiceServiceVoipParser())
