"""Microsoft Teams PowerShell evidence parsers."""

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

__all__ = [
    "MicrosoftGetCsAutoAttendantParser",
    "MicrosoftGetCsCallQueueParser",
    "MicrosoftGetCsOnlineUserParser",
    "MicrosoftGetCsOnlineLisLocationParser",
    "MicrosoftGetCsOnlinePstnGatewayParser",
    "MicrosoftGetCsOnlinePstnUsageParser",
    "MicrosoftGetCsOnlineVoiceRouteParser",
    "MicrosoftGetCsOnlineVoiceRoutingPolicyParser",
    "MicrosoftGetCsPhoneNumberAssignmentParser",
    "MicrosoftGetCsResourceAccountParser",
    "MicrosoftGetCsTenantDialPlanParser",
]
