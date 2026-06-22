"""Microsoft Teams parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.microsoft.parser.teams.get_csautoattendant import MicrosoftGetCsAutoAttendantParser
from plugins.microsoft.parser.teams.get_cscallqueue import MicrosoftGetCsCallQueueParser
from plugins.microsoft.parser.teams.get_csonlineuser import MicrosoftGetCsOnlineUserParser
from plugins.microsoft.parser.teams.get_csonlinelislocation import MicrosoftGetCsOnlineLisLocationParser
from plugins.microsoft.parser.teams.get_csonlinepstngateway import MicrosoftGetCsOnlinePstnGatewayParser
from plugins.microsoft.parser.teams.get_csonlinepstnusage import MicrosoftGetCsOnlinePstnUsageParser
from plugins.microsoft.parser.teams.get_csonlinevoiceroute import MicrosoftGetCsOnlineVoiceRouteParser
from plugins.microsoft.parser.teams.get_csonlinevoiceroutingpolicy import MicrosoftGetCsOnlineVoiceRoutingPolicyParser
from plugins.microsoft.parser.teams.get_csphonenumberassignment import MicrosoftGetCsPhoneNumberAssignmentParser
from plugins.microsoft.parser.teams.get_csresourceaccount import MicrosoftGetCsResourceAccountParser
from plugins.microsoft.parser.teams.get_cstenantdialplan import MicrosoftGetCsTenantDialPlanParser


def register_teams_parsers(registry: ParserRegistry) -> None:
    """Register all Microsoft Teams PowerShell parsers."""
    registry.register(MicrosoftGetCsOnlineUserParser())
    registry.register(MicrosoftGetCsPhoneNumberAssignmentParser())
    registry.register(MicrosoftGetCsOnlineVoiceRoutingPolicyParser())
    registry.register(MicrosoftGetCsOnlineVoiceRouteParser())
    registry.register(MicrosoftGetCsTenantDialPlanParser())
    registry.register(MicrosoftGetCsOnlinePstnGatewayParser())
    registry.register(MicrosoftGetCsOnlinePstnUsageParser())
    registry.register(MicrosoftGetCsCallQueueParser())
    registry.register(MicrosoftGetCsAutoAttendantParser())
    registry.register(MicrosoftGetCsResourceAccountParser())
    registry.register(MicrosoftGetCsOnlineLisLocationParser())
