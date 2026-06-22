"""Microsoft Teams discovery planner rules."""

from __future__ import annotations

from dataclasses import dataclass

from discovery.planner_models import DiscoveryPriority, DiscoveryRequest
from discovery.planner_rule import DiscoveryPlannerRule
from discovery.planner_rules import collected_commands, related_hypothesis_titles, _request_id
from domain.models import Case
from runtime.teams_investigation import VP_TEAMS_0001_PLAYBOOK_ID

ONLINE_USER_COMMAND = "get-csonlineuser"
VOICE_ROUTING_POLICY_COMMAND = "get-csonlinevoiceroutingpolicy"
VOICE_ROUTE_COMMAND = "get-csonlinevoiceroute"
PSTN_GATEWAY_COMMAND = "get-csonlinepstngateway"
PHONE_NUMBER_COMMAND = "get-csphonenumberassignment"
LIS_LOCATION_COMMAND = "get-csonlinelislocation"
RESOURCE_ACCOUNT_COMMAND = "get-csresourceaccount"


def _teams_case(case: Case) -> bool:
    return case.playbook_id == VP_TEAMS_0001_PLAYBOOK_ID


@dataclass(frozen=True)
class TeamsOnlineUserMissingRule(DiscoveryPlannerRule):
    id: str = "teams_online_user_missing"
    title: str = "Teams online user export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or ONLINE_USER_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=ONLINE_USER_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.CRITICAL,
            reason="Teams user licensing and Enterprise Voice state are not confirmed.",
            estimated_confidence_gain=20.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("license", "enterprise voice", "phone number"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsVoiceRoutingPolicyMissingRule(DiscoveryPlannerRule):
    id: str = "teams_voice_routing_policy_missing"
    title: str = "Voice routing policy export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or VOICE_ROUTING_POLICY_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=VOICE_ROUTING_POLICY_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.HIGH,
            reason="Voice routing policy and PSTN usage assignments are not available.",
            estimated_confidence_gain=16.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("routing", "pstn", "voice route"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsVoiceRouteMissingRule(DiscoveryPlannerRule):
    id: str = "teams_voice_route_missing"
    title: str = "Voice route export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or VOICE_ROUTE_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=VOICE_ROUTE_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.HIGH,
            reason="Online voice route and PSTN gateway references are not confirmed.",
            estimated_confidence_gain=14.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("voice route", "routing", "pstn"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsPstnGatewayMissingRule(DiscoveryPlannerRule):
    id: str = "teams_pstn_gateway_missing"
    title: str = "PSTN gateway export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or PSTN_GATEWAY_COMMAND in collected_commands(case):
            return None
        related = related_hypothesis_titles(
            case,
            keywords=("sbc", "direct routing", "tls", "sip options"),
        )
        if not related and ONLINE_USER_COMMAND not in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=PSTN_GATEWAY_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.HIGH,
            reason="Direct Routing SBC health has not been validated.",
            estimated_confidence_gain=18.0,
            estimated_minutes=2,
            related_hypotheses=related,
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsPhoneNumberMissingRule(DiscoveryPlannerRule):
    id: str = "teams_phone_number_missing"
    title: str = "Phone number assignment export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or PHONE_NUMBER_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=PHONE_NUMBER_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.MEDIUM,
            reason="Telephone number assignment status is not confirmed.",
            estimated_confidence_gain=12.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("phone number", "assignment"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsLisLocationMissingRule(DiscoveryPlannerRule):
    id: str = "teams_lis_location_missing"
    title: str = "LIS location export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or LIS_LOCATION_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=LIS_LOCATION_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.HIGH,
            reason="Emergency location data has not been collected.",
            estimated_confidence_gain=15.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("emergency", "e911", "lis"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class TeamsResourceAccountMissingRule(DiscoveryPlannerRule):
    id: str = "teams_resource_account_missing"
    title: str = "Resource account export missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _teams_case(case) or RESOURCE_ACCOUNT_COMMAND in collected_commands(case):
            return None
        related = related_hypothesis_titles(
            case,
            keywords=("resource account", "auto attendant", "call queue"),
        )
        if not related:
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=RESOURCE_ACCOUNT_COMMAND,
            vendor="microsoft",
            priority=DiscoveryPriority.MEDIUM,
            reason="Resource account licensing and phone number are not confirmed.",
            estimated_confidence_gain=10.0,
            estimated_minutes=2,
            related_hypotheses=related,
            already_collected=False,
            optional=True,
        )


TEAMS_DISCOVERY_RULES: tuple[DiscoveryPlannerRule, ...] = (
    TeamsOnlineUserMissingRule(),
    TeamsVoiceRoutingPolicyMissingRule(),
    TeamsVoiceRouteMissingRule(),
    TeamsPstnGatewayMissingRule(),
    TeamsPhoneNumberMissingRule(),
    TeamsLisLocationMissingRule(),
    TeamsResourceAccountMissingRule(),
)


def register_teams_discovery_rules(registry) -> None:
    """Register Microsoft Teams discovery planner rules."""
    for rule in TEAMS_DISCOVERY_RULES:
        registry.register_rule(rule)
