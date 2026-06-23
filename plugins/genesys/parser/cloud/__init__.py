"""Genesys Cloud parser pack registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.genesys.parser.cloud.agents_export import GenesysAgentsExportParser
from plugins.genesys.parser.cloud.architect_export import GenesysArchitectExportParser
from plugins.genesys.parser.cloud.byoc_cloud_trunks_export import GenesysByocCloudTrunksExportParser
from plugins.genesys.parser.cloud.byoc_premises_trunks_export import GenesysByocPremisesTrunksExportParser
from plugins.genesys.parser.cloud.campaigns_export import GenesysCampaignsExportParser
from plugins.genesys.parser.cloud.data_actions_export import GenesysDataActionsExportParser
from plugins.genesys.parser.cloud.edge_devices_export import GenesysEdgeDevicesExportParser
from plugins.genesys.parser.cloud.flows_export import GenesysFlowsExportParser
from plugins.genesys.parser.cloud.organization_export import GenesysOrganizationExportParser
from plugins.genesys.parser.cloud.presence_export import GenesysPresenceExportParser
from plugins.genesys.parser.cloud.queue_members_export import GenesysQueueMembersExportParser
from plugins.genesys.parser.cloud.queues_export import GenesysQueuesExportParser
from plugins.genesys.parser.cloud.recording_policies_export import GenesysRecordingPoliciesExportParser
from plugins.genesys.parser.cloud.skills_export import GenesysSkillsExportParser
from plugins.genesys.parser.cloud.users_export import GenesysUsersExportParser


def register_genesys_cloud_parsers(registry: ParserRegistry) -> None:
    """Register all Genesys Cloud export parsers."""
    registry.register(GenesysOrganizationExportParser())
    registry.register(GenesysUsersExportParser())
    registry.register(GenesysQueuesExportParser())
    registry.register(GenesysQueueMembersExportParser())
    registry.register(GenesysAgentsExportParser())
    registry.register(GenesysPresenceExportParser())
    registry.register(GenesysFlowsExportParser())
    registry.register(GenesysArchitectExportParser())
    registry.register(GenesysDataActionsExportParser())
    registry.register(GenesysByocCloudTrunksExportParser())
    registry.register(GenesysByocPremisesTrunksExportParser())
    registry.register(GenesysEdgeDevicesExportParser())
    registry.register(GenesysRecordingPoliciesExportParser())
    registry.register(GenesysCampaignsExportParser())
    registry.register(GenesysSkillsExportParser())
