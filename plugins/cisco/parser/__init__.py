"""Cisco parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.cisco.parser.debug_ccsip_messages import CiscoDebugCcsipMessagesParser
from plugins.cisco.parser.show_dial_peer_voice_summary import CiscoShowDialPeerVoiceSummaryParser
from plugins.cisco.parser.show_run_voice_service_voip import CiscoShowRunVoiceServiceVoipParser
from plugins.cisco.parser.show_sip_ua_status import CiscoShowSipUaStatusParser
from plugins.cisco.parser.cucm.show_risdb import CiscoShowRisdbParser
from plugins.cisco.parser.cucm.utils_dbreplication import CiscoUtilsDbReplicationParser
from plugins.cisco.parser.cucm.utils_service_list import CiscoUtilsServiceListParser
from plugins.cisco.parser.cucm.show_cert_list import CiscoShowCertListParser
from plugins.cisco.parser.cucm.show_route_plan import CiscoShowRoutePlanParser
from plugins.cisco.parser.cucm.show_sip_trunk import CiscoShowSipTrunkParser


def register_cisco_parsers(registry: ParserRegistry) -> None:
    """Register all Cisco command parsers with the given registry."""
    registry.register(CiscoShowSipUaStatusParser())
    registry.register(CiscoDebugCcsipMessagesParser())
    registry.register(CiscoShowDialPeerVoiceSummaryParser())
    registry.register(CiscoShowRunVoiceServiceVoipParser())
    registry.register(CiscoShowRisdbParser())
    registry.register(CiscoUtilsDbReplicationParser())
    registry.register(CiscoUtilsServiceListParser())
    registry.register(CiscoShowCertListParser())
    registry.register(CiscoShowRoutePlanParser())
    registry.register(CiscoShowSipTrunkParser())
