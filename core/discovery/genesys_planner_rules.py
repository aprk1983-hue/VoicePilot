"""Genesys Cloud discovery planner rules."""

from __future__ import annotations

from dataclasses import dataclass

from discovery.planner_models import DiscoveryPriority, DiscoveryRequest
from discovery.planner_rule import DiscoveryPlannerRule
from discovery.planner_rules import collected_commands, related_hypothesis_titles, _request_id
from domain.models import Case
from runtime.genesys_investigation import VP_GENESYS_0001_PLAYBOOK_ID

ORGANIZATION_EXPORT = "organization-export"
USERS_EXPORT = "users-export"
QUEUES_EXPORT = "queues-export"
QUEUE_MEMBERS_EXPORT = "queue-members-export"
AGENTS_EXPORT = "agents-export"
PRESENCE_EXPORT = "presence-export"
FLOWS_EXPORT = "flows-export"
ARCHITECT_EXPORT = "architect-export"
DATA_ACTIONS_EXPORT = "data-actions-export"
BYOC_CLOUD_EXPORT = "byoc-cloud-trunks-export"
BYOC_PREMISES_EXPORT = "byoc-premises-trunks-export"
EDGE_DEVICES_EXPORT = "edge-devices-export"
RECORDING_POLICIES_EXPORT = "recording-policies-export"
CAMPAIGNS_EXPORT = "campaigns-export"
SKILLS_EXPORT = "skills-export"


def _genesys_case(case: Case) -> bool:
    return case.playbook_id == VP_GENESYS_0001_PLAYBOOK_ID


def _missing_rule(
    rule_id: str,
    title: str,
    command: str,
    *,
    priority: DiscoveryPriority,
    reason: str,
    gain: float,
    keywords: tuple[str, ...],
    optional: bool = False,
    case: Case,
) -> DiscoveryRequest:
    return DiscoveryRequest(
        request_id=_request_id(rule_id),
        command=command,
        vendor="genesys",
        priority=priority,
        reason=reason,
        estimated_confidence_gain=gain,
        estimated_minutes=2,
        related_hypotheses=related_hypothesis_titles(case, keywords=keywords),
        already_collected=False,
        optional=optional,
    )


@dataclass(frozen=True)
class GenesysOrganizationExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_organization_export_missing"
    title: str = "Organization export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or ORGANIZATION_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, ORGANIZATION_EXPORT,
            priority=DiscoveryPriority.CRITICAL,
            reason="Organization authentication and service state are not confirmed.",
            gain=18.0,
            keywords=("oauth", "token", "organization"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysUsersExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_users_export_missing"
    title: str = "Users export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or USERS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, USERS_EXPORT,
            priority=DiscoveryPriority.MEDIUM,
            reason="User licensing and routing assignments are not available.",
            gain=10.0,
            keywords=("agent", "user"),
            optional=True,
            case=case,
        )


@dataclass(frozen=True)
class GenesysQueuesExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_queues_export_missing"
    title: str = "Queues export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or QUEUES_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, QUEUES_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="ACD queue availability and load are not confirmed.",
            gain=16.0,
            keywords=("queue", "acd"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysQueueMembersExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_queue_members_export_missing"
    title: str = "Queue members export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or QUEUE_MEMBERS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, QUEUE_MEMBERS_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Queue member availability is not confirmed.",
            gain=14.0,
            keywords=("queue", "member"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysAgentsExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_agents_export_missing"
    title: str = "Agents export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or AGENTS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, AGENTS_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Agent login and interaction state are not available.",
            gain=15.0,
            keywords=("agent", "logged in", "interacting"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysPresenceExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_presence_export_missing"
    title: str = "Presence export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or PRESENCE_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, PRESENCE_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Presence synchronization and routing status are not confirmed.",
            gain=14.0,
            keywords=("presence", "routing"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysFlowsExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_flows_export_missing"
    title: str = "Flows export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or FLOWS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, FLOWS_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Inbound call flow health is not confirmed.",
            gain=14.0,
            keywords=("flow", "architect"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysArchitectExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_architect_export_missing"
    title: str = "Architect export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or ARCHITECT_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, ARCHITECT_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Architect publish state is not available.",
            gain=13.0,
            keywords=("architect", "publish"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysDataActionsExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_data_actions_export_missing"
    title: str = "Data Actions export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or DATA_ACTIONS_EXPORT in collected_commands(case):
            return None
        related = related_hypothesis_titles(case, keywords=("data action", "integration", "flow"))
        if not related and ARCHITECT_EXPORT not in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, DATA_ACTIONS_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="Architect Data Action availability is not confirmed.",
            gain=12.0,
            keywords=("data action", "integration"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysByocCloudExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_byoc_cloud_export_missing"
    title: str = "BYOC Cloud trunks export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or BYOC_CLOUD_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, BYOC_CLOUD_EXPORT,
            priority=DiscoveryPriority.CRITICAL,
            reason="BYOC Cloud trunk and SIP OPTIONS state are not confirmed.",
            gain=18.0,
            keywords=("byoc", "trunk", "sip options", "carrier"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysByocPremisesExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_byoc_premises_export_missing"
    title: str = "BYOC Premises trunks export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or BYOC_PREMISES_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, BYOC_PREMISES_EXPORT,
            priority=DiscoveryPriority.HIGH,
            reason="BYOC Premises trunk and Edge association are not confirmed.",
            gain=15.0,
            keywords=("byoc", "premises", "edge"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysEdgeDevicesExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_edge_devices_export_missing"
    title: str = "Edge devices export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or EDGE_DEVICES_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, EDGE_DEVICES_EXPORT,
            priority=DiscoveryPriority.CRITICAL,
            reason="Genesys Cloud Edge availability is not confirmed.",
            gain=17.0,
            keywords=("edge", "offline"),
            case=case,
        )


@dataclass(frozen=True)
class GenesysRecordingPoliciesExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_recording_policies_export_missing"
    title: str = "Recording policies export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or RECORDING_POLICIES_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, RECORDING_POLICIES_EXPORT,
            priority=DiscoveryPriority.MEDIUM,
            reason="Recording policy health is not confirmed.",
            gain=10.0,
            keywords=("recording",),
            optional=True,
            case=case,
        )


@dataclass(frozen=True)
class GenesysCampaignsExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_campaigns_export_missing"
    title: str = "Campaigns export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or CAMPAIGNS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, CAMPAIGNS_EXPORT,
            priority=DiscoveryPriority.MEDIUM,
            reason="Outbound campaign state is not confirmed.",
            gain=10.0,
            keywords=("campaign", "outbound"),
            optional=True,
            case=case,
        )


@dataclass(frozen=True)
class GenesysSkillsExportMissingRule(DiscoveryPlannerRule):
    id: str = "genesys_skills_export_missing"
    title: str = "Skills export evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _genesys_case(case) or SKILLS_EXPORT in collected_commands(case):
            return None
        return _missing_rule(
            self.id, self.title, SKILLS_EXPORT,
            priority=DiscoveryPriority.LOW,
            reason="Skill-based routing configuration is not confirmed.",
            gain=8.0,
            keywords=("skill", "routing"),
            optional=True,
            case=case,
        )


GENESYS_DISCOVERY_RULES: tuple[DiscoveryPlannerRule, ...] = (
    GenesysOrganizationExportMissingRule(),
    GenesysUsersExportMissingRule(),
    GenesysQueuesExportMissingRule(),
    GenesysQueueMembersExportMissingRule(),
    GenesysAgentsExportMissingRule(),
    GenesysPresenceExportMissingRule(),
    GenesysFlowsExportMissingRule(),
    GenesysArchitectExportMissingRule(),
    GenesysDataActionsExportMissingRule(),
    GenesysByocCloudExportMissingRule(),
    GenesysByocPremisesExportMissingRule(),
    GenesysEdgeDevicesExportMissingRule(),
    GenesysRecordingPoliciesExportMissingRule(),
    GenesysCampaignsExportMissingRule(),
    GenesysSkillsExportMissingRule(),
)


def register_genesys_discovery_rules(registry) -> None:
    """Register Genesys Cloud discovery planner rules."""
    for rule in GENESYS_DISCOVERY_RULES:
        registry.register_rule(rule)
