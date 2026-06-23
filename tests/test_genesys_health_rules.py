"""Tests for Genesys Cloud health rules."""

from __future__ import annotations

import json

import pytest

from health import HealthCategory, HealthEngine, HealthSeverity, HealthStatus, default_health_rule_registry
from health.genesys_rules import GENESYS_HEALTH_RULES
from model.genesys_objects import (
    Agent,
    ArchitectFlow,
    ByocCloudTrunk,
    ByocPremisesTrunk,
    Campaign,
    DataAction,
    EdgeDevice,
    GenesysOrganization,
    PresenceDefinition,
    Queue,
    QueueMember,
    Recording,
    RecordingPolicy,
    SipEndpoint,
    UserRoutingStatus,
)
from topology.topology_builder import TopologyBuilder

_BASE = {
    "vendor": "genesys",
    "platform": "Genesys Cloud",
    "hostname": "acme.mypurecloud.com",
    "source_evidence_id": "EVD-gc-health-001",
}


def _prov(parser: str, command: str) -> dict[str, str]:
    return {**_BASE, "source_parser": parser, "source_command": command}


def _healthy_objects() -> list:
    organization = GenesysOrganization.create(
        **_prov("genesys_organization_export", "organization-export"),
        object_id="VOBJ-gc-org-001",
        organization_id="org-100",
        organization_name="Acme CC",
        state="Active",
        domain="acme.mypurecloud.com",
        metadata={
            "oauth_status": "Success",
            "token_status": "Valid",
            "media_service_status": "Available",
            "conversation_service_status": "Available",
            "analytics_status": "Available",
            "webrtc_status": "Available",
        },
    )
    agent = Agent.create(
        **_prov("genesys_agents_export", "agents-export"),
        object_id="VOBJ-gc-agent-001",
        agent_id="agent-001",
        display_name="Alex Agent",
        state="On Queue",
        queue_id="queue-100",
    )
    presence = PresenceDefinition.create(
        **_prov("genesys_presence_export", "presence-export"),
        object_id="VOBJ-gc-pres-001",
        presence_id="pres-01",
        presence_name="Available",
        system_presence="true",
        metadata={"sync_state": "Synchronized"},
    )
    routing = UserRoutingStatus.create(
        **_prov("genesys_presence_export", "presence-export"),
        object_id="VOBJ-gc-route-001",
        user_id="user-001",
        routing_status="On Queue",
        presence_id="pres-01",
    )
    queue = Queue.create(
        **_prov("genesys_queues_export", "queues-export"),
        object_id="VOBJ-gc-queue-001",
        queue_id="queue-100",
        queue_name="Sales ACD",
        state="Active",
        metadata={"waiting_calls": "5", "queue_capacity_threshold": "100"},
    )
    member = QueueMember.create(
        **_prov("genesys_queue_members_export", "queue-members-export"),
        object_id="VOBJ-gc-member-001",
        member_id="member-01",
        queue_id="queue-100",
        user_id="user-001",
        state="Active",
    )
    cloud_trunk = ByocCloudTrunk.create(
        **_prov("genesys_byoc_cloud_trunks_export", "byoc-cloud-trunks-export"),
        object_id="VOBJ-gc-trunk-cloud-001",
        trunk_id="trunk-cloud-01",
        trunk_name="BYOC Cloud Primary",
        state="Active",
        sip_options_status="Success",
    )
    premises_trunk = ByocPremisesTrunk.create(
        **_prov("genesys_byoc_premises_trunks_export", "byoc-premises-trunks-export"),
        object_id="VOBJ-gc-trunk-prem-001",
        trunk_id="trunk-prem-01",
        trunk_name="BYOC Premises Primary",
        state="Active",
        edge_id="edge-900",
    )
    endpoint = SipEndpoint.create(
        **_prov("genesys_byoc_cloud_trunks_export", "byoc-cloud-trunks-export"),
        object_id="VOBJ-gc-endpoint-001",
        endpoint_id="endpoint-01",
        endpoint_name="Carrier SIP",
        address="203.0.113.10",
        transport="TLS",
        metadata={"certificate_status": "Valid", "tls_status": "Negotiated"},
    )
    architect = ArchitectFlow.create(
        **_prov("genesys_architect_export", "architect-export"),
        object_id="VOBJ-gc-arch-001",
        flow_id="arch-300",
        flow_name="Sales IVR",
        publish_state="Published",
        data_action_id="da-500",
    )
    data_action = DataAction.create(
        **_prov("genesys_data_actions_export", "data-actions-export"),
        object_id="VOBJ-gc-da-001",
        action_id="da-500",
        action_name="CRM Lookup",
        state="Active",
        endpoint_url="https://crm.example.com/api",
    )
    recording_policy = RecordingPolicy.create(
        **_prov("genesys_recording_policies_export", "recording-policies-export"),
        object_id="VOBJ-gc-rec-pol-001",
        policy_id="rec-pol-01",
        policy_name="Sales Recording",
        state="Active",
    )
    recording = Recording.create(
        **_prov("genesys_recording_policies_export", "recording-policies-export"),
        object_id="VOBJ-gc-rec-001",
        recording_id="rec-001",
        policy_id="rec-pol-01",
        state="Active",
    )
    campaign = Campaign.create(
        **_prov("genesys_campaigns_export", "campaigns-export"),
        object_id="VOBJ-gc-camp-001",
        campaign_id="camp-700",
        campaign_name="Outbound Sales",
        state="Running",
        queue_id="queue-100",
    )
    edge = EdgeDevice.create(
        **_prov("genesys_edge_devices_export", "edge-devices-export"),
        object_id="VOBJ-gc-edge-001",
        edge_id="edge-900",
        edge_name="Edge-West-01",
        state="Online",
        organization_id="org-100",
    )
    return [
        organization,
        agent,
        presence,
        routing,
        queue,
        member,
        cloud_trunk,
        premises_trunk,
        endpoint,
        architect,
        data_action,
        recording_policy,
        recording,
        campaign,
        edge,
    ]


def _healthy_topology():
    return TopologyBuilder().build(_healthy_objects())


def _unhealthy_topology():
    objects = _healthy_objects()
    replacements = {
        "VOBJ-gc-org-001": GenesysOrganization.create(
            **_prov("genesys_organization_export", "organization-export"),
            object_id="VOBJ-gc-org-001",
            organization_id="org-100",
            organization_name="Acme CC",
            state="Unavailable",
            metadata={
                "oauth_failure": True,
                "token_expired": True,
                "organization_unavailable": True,
                "media_service_unavailable": True,
                "conversation_service_unavailable": True,
                "analytics_service_unavailable": True,
                "webrtc_failure": True,
                "oauth_status": "failed",
                "token_status": "expired",
                "media_service_status": "down",
                "conversation_service_status": "failed",
                "analytics_status": "unavailable",
                "webrtc_status": "failed",
            },
        ),
        "VOBJ-gc-agent-001": Agent.create(
            **_prov("genesys_agents_export", "agents-export"),
            object_id="VOBJ-gc-agent-001",
            agent_id="agent-001",
            display_name="Alex Agent",
            state="Interacting",
            queue_id="queue-100",
            metadata={"agent_not_logged_in": True, "agent_stuck_interacting": True, "webrtc_failure": True},
        ),
        "VOBJ-gc-pres-001": PresenceDefinition.create(
            **_prov("genesys_presence_export", "presence-export"),
            object_id="VOBJ-gc-pres-001",
            presence_id="pres-01",
            presence_name="Available",
            metadata={"presence_sync_failure": True, "sync_state": "out_of_sync"},
        ),
        "VOBJ-gc-route-001": UserRoutingStatus.create(
            **_prov("genesys_presence_export", "presence-export"),
            object_id="VOBJ-gc-route-001",
            user_id="user-001",
            routing_status="Disabled",
            metadata={"user_routing_disabled": True, "presence_sync_failure": True},
        ),
        "VOBJ-gc-queue-001": Queue.create(
            **_prov("genesys_queues_export", "queues-export"),
            object_id="VOBJ-gc-queue-001",
            queue_id="queue-100",
            queue_name="Sales ACD",
            state="Unavailable",
            metadata={"queue_unavailable": True, "queue_overloaded": True, "queue_no_members": True, "waiting_calls": "75"},
        ),
        "VOBJ-gc-member-001": QueueMember.create(
            **_prov("genesys_queue_members_export", "queue-members-export"),
            object_id="VOBJ-gc-member-001",
            member_id="member-01",
            queue_id="queue-100",
            user_id="user-001",
            state="Unavailable",
            metadata={"queue_member_unavailable": True},
        ),
        "VOBJ-gc-trunk-cloud-001": ByocCloudTrunk.create(
            **_prov("genesys_byoc_cloud_trunks_export", "byoc-cloud-trunks-export"),
            object_id="VOBJ-gc-trunk-cloud-001",
            trunk_id="trunk-cloud-01",
            trunk_name="BYOC Cloud Primary",
            state="Down",
            sip_options_status="Failed",
            metadata={"byoc_cloud_unavailable": True, "sip_options_failure": True, "carrier_unreachable": True},
        ),
        "VOBJ-gc-trunk-prem-001": ByocPremisesTrunk.create(
            **_prov("genesys_byoc_premises_trunks_export", "byoc-premises-trunks-export"),
            object_id="VOBJ-gc-trunk-prem-001",
            trunk_id="trunk-prem-01",
            trunk_name="BYOC Premises Primary",
            state="Unavailable",
            edge_id="edge-900",
            metadata={"byoc_premises_unavailable": True, "carrier_unreachable": True},
        ),
        "VOBJ-gc-endpoint-001": SipEndpoint.create(
            **_prov("genesys_byoc_cloud_trunks_export", "byoc-cloud-trunks-export"),
            object_id="VOBJ-gc-endpoint-001",
            endpoint_id="endpoint-01",
            endpoint_name="Carrier SIP",
            address=None,
            transport="TLS",
            metadata={
                "sip_options_failure": True,
                "carrier_unreachable": True,
                "tls_certificate_expired": True,
                "tls_negotiation_failure": True,
                "certificate_status": "expired",
                "tls_status": "failed",
            },
        ),
        "VOBJ-gc-arch-001": ArchitectFlow.create(
            **_prov("genesys_architect_export", "architect-export"),
            object_id="VOBJ-gc-arch-001",
            flow_id="arch-300",
            flow_name="Sales IVR",
            publish_state="Failed",
            metadata={"architect_publish_failure": True},
        ),
        "VOBJ-gc-da-001": DataAction.create(
            **_prov("genesys_data_actions_export", "data-actions-export"),
            object_id="VOBJ-gc-da-001",
            action_id="da-500",
            action_name="CRM Lookup",
            state="Failed",
            endpoint_url=None,
            metadata={"data_action_failure": True},
        ),
        "VOBJ-gc-rec-pol-001": RecordingPolicy.create(
            **_prov("genesys_recording_policies_export", "recording-policies-export"),
            object_id="VOBJ-gc-rec-pol-001",
            policy_id="rec-pol-01",
            policy_name="Sales Recording",
            state="Failed",
            metadata={"recording_failure": True},
        ),
        "VOBJ-gc-rec-001": Recording.create(
            **_prov("genesys_recording_policies_export", "recording-policies-export"),
            object_id="VOBJ-gc-rec-001",
            recording_id="rec-001",
            policy_id="rec-pol-01",
            state="Failed",
            metadata={"recording_failure": True},
        ),
        "VOBJ-gc-camp-001": Campaign.create(
            **_prov("genesys_campaigns_export", "campaigns-export"),
            object_id="VOBJ-gc-camp-001",
            campaign_id="camp-700",
            campaign_name="Outbound Sales",
            state="Failed",
            metadata={"outbound_campaign_failure": True},
        ),
        "VOBJ-gc-edge-001": EdgeDevice.create(
            **_prov("genesys_edge_devices_export", "edge-devices-export"),
            object_id="VOBJ-gc-edge-001",
            edge_id="edge-900",
            edge_name="Edge-West-01",
            state="Offline",
            metadata={"edge_offline": True, "edge_degraded": True},
        ),
    }
    return TopologyBuilder().build([replacements.get(obj.id, obj) for obj in objects])


class TestGenesysRuleRegistration:
    def test_default_registry_includes_genesys_rules(self) -> None:
        registry = default_health_rule_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert "genesys_oauth_failure" in rule_ids
        assert "genesys_edge_offline" in rule_ids
        assert len(GENESYS_HEALTH_RULES) == 27

    @pytest.mark.parametrize("rule", GENESYS_HEALTH_RULES, ids=lambda rule: rule.id)
    def test_every_genesys_rule_evaluates(self, rule) -> None:
        topology = _unhealthy_topology()
        target = next(
            obj for obj in topology.all_objects() if obj.object_type in rule.supported_object_types
        )
        result = rule.evaluate(target, topology)
        assert result.rule_id == rule.id
        assert result.status in {HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL}
        assert result.recommendation is None


class TestAuthenticationRules:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "genesys_oauth_failure",
            "genesys_token_expired",
            "genesys_organization_unavailable",
        ],
    )
    def test_authentication_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        organization = topology.genesys_organizations[0]
        result = next(
            item for item in HealthEngine().evaluate_object(organization, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL
        assert result.category in {HealthCategory.SECURITY, HealthCategory.CONFIGURATION}


class TestAgentRules:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "genesys_agent_not_logged_in",
            "genesys_agent_stuck_interacting",
        ],
    )
    def test_agent_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        agent = topology.genesys_agents[0]
        result = next(
            item for item in HealthEngine().evaluate_object(agent, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_presence_sync_failure_on_presence(self) -> None:
        topology = _unhealthy_topology()
        presence = next(obj for obj in topology.genesys_agents if isinstance(obj, PresenceDefinition))
        result = next(
            item
            for item in HealthEngine().evaluate_object(presence, topology)
            if item.rule_id == "genesys_presence_sync_failure"
        )
        assert result.status == HealthStatus.FAIL

    def test_user_routing_disabled_fails(self) -> None:
        topology = _unhealthy_topology()
        routing = next(obj for obj in topology.genesys_agents if isinstance(obj, UserRoutingStatus))
        result = next(
            item
            for item in HealthEngine().evaluate_object(routing, topology)
            if item.rule_id == "genesys_user_routing_disabled"
        )
        assert result.status == HealthStatus.FAIL


class TestQueueRules:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "genesys_queue_unavailable",
            "genesys_queue_overloaded",
        ],
    )
    def test_queue_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        queue = next(obj for obj in topology.genesys_queues if isinstance(obj, Queue))
        result = next(
            item for item in HealthEngine().evaluate_object(queue, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_queue_member_unavailable_fails(self) -> None:
        topology = _unhealthy_topology()
        member = next(obj for obj in topology.genesys_queues if isinstance(obj, QueueMember))
        result = next(
            item
            for item in HealthEngine().evaluate_object(member, topology)
            if item.rule_id == "genesys_queue_member_unavailable"
        )
        assert result.status == HealthStatus.FAIL

    def test_queue_no_members_fails_without_members(self) -> None:
        topology = TopologyBuilder().build(
            [obj for obj in _healthy_objects() if not isinstance(obj, QueueMember)]
        )
        queue = next(obj for obj in topology.genesys_queues if isinstance(obj, Queue))
        result = next(
            item
            for item in HealthEngine().evaluate_object(queue, topology)
            if item.rule_id == "genesys_queue_no_members"
        )
        assert result.status == HealthStatus.FAIL


class TestVoiceRoutingRules:
    @pytest.mark.parametrize(
        ("rule_id", "object_id"),
        [
            ("genesys_byoc_cloud_unavailable", "VOBJ-gc-trunk-cloud-001"),
            ("genesys_sip_options_failure", "VOBJ-gc-trunk-cloud-001"),
            ("genesys_carrier_unreachable", "VOBJ-gc-trunk-cloud-001"),
            ("genesys_byoc_premises_unavailable", "VOBJ-gc-trunk-prem-001"),
            ("genesys_tls_certificate_expired", "VOBJ-gc-endpoint-001"),
            ("genesys_tls_negotiation_failure", "VOBJ-gc-endpoint-001"),
        ],
    )
    def test_voice_routing_rule_fails(self, rule_id: str, object_id: str) -> None:
        topology = _unhealthy_topology()
        target = next(obj for obj in topology.all_objects() if obj.id == object_id)
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL


class TestArchitectRules:
    def test_architect_publish_failure(self) -> None:
        topology = _unhealthy_topology()
        flow = next(obj for obj in topology.genesys_flows if isinstance(obj, ArchitectFlow))
        result = next(
            item
            for item in HealthEngine().evaluate_object(flow, topology)
            if item.rule_id == "genesys_architect_publish_failure"
        )
        assert result.status == HealthStatus.FAIL

    def test_data_action_failure(self) -> None:
        topology = _unhealthy_topology()
        action = next(obj for obj in topology.genesys_flows if isinstance(obj, DataAction))
        result = next(
            item
            for item in HealthEngine().evaluate_object(action, topology)
            if item.rule_id == "genesys_data_action_failure"
        )
        assert result.status == HealthStatus.FAIL


class TestMediaRules:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "genesys_media_service_unavailable",
            "genesys_conversation_service_unavailable",
            "genesys_analytics_service_unavailable",
        ],
    )
    def test_organization_service_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        organization = topology.genesys_organizations[0]
        result = next(
            item for item in HealthEngine().evaluate_object(organization, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_webrtc_failure_on_organization(self) -> None:
        topology = _unhealthy_topology()
        organization = topology.genesys_organizations[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(organization, topology)
            if item.rule_id == "genesys_webrtc_failure"
        )
        assert result.status == HealthStatus.FAIL

    def test_recording_failure_on_policy(self) -> None:
        topology = _unhealthy_topology()
        policy = topology.genesys_recordings[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(policy, topology)
            if item.rule_id == "genesys_recording_failure"
        )
        assert result.status == HealthStatus.FAIL


class TestCampaignAndInfrastructureRules:
    def test_outbound_campaign_failure(self) -> None:
        topology = _unhealthy_topology()
        campaign = topology.genesys_campaigns[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(campaign, topology)
            if item.rule_id == "genesys_outbound_campaign_failure"
        )
        assert result.status == HealthStatus.FAIL

    @pytest.mark.parametrize(
        "rule_id",
        ["genesys_edge_offline", "genesys_edge_degraded"],
    )
    def test_edge_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        edge = topology.genesys_edges[0]
        result = next(
            item for item in HealthEngine().evaluate_object(edge, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL


class TestHealthyTopology:
    def test_healthy_topology_has_no_genesys_failures(self) -> None:
        report = HealthEngine().evaluate_topology(_healthy_topology())
        genesys_results = [
            result for result in report.results if result.object_type.startswith("genesys_")
        ]
        assert genesys_results
        assert all(result.status == HealthStatus.PASS for result in genesys_results)

    def test_healthy_organization_passes_auth_rules(self) -> None:
        topology = _healthy_topology()
        organization = topology.genesys_organizations[0]
        results = {
            item.rule_id: item
            for item in HealthEngine().evaluate_object(organization, topology)
            if item.rule_id
            in {
                "genesys_oauth_failure",
                "genesys_token_expired",
                "genesys_organization_unavailable",
            }
        }
        assert all(result.status == HealthStatus.PASS for result in results.values())


class TestHealthEngineIntegration:
    def test_multiple_simultaneous_failures_reduce_score(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        failures = [
            result
            for result in report.results
            if result.object_type.startswith("genesys_") and result.status == HealthStatus.FAIL
        ]
        assert len(failures) >= 20
        assert report.overall_score < 50
        assert report.fail_count >= 20

    def test_severity_ordering_in_aggregation(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        severities = dict(report.severity_counts)
        assert severities.get("critical", 0) >= 5
        assert severities.get("high", 0) >= 10

    def test_deterministic_result_ordering(self) -> None:
        engine = HealthEngine()
        topology = _unhealthy_topology()
        first = engine.evaluate_topology(topology)
        second = engine.evaluate_topology(topology)
        assert first.results == second.results

    def test_genesys_results_have_no_recommendations(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        genesys_results = [
            result for result in report.results if result.object_type.startswith("genesys_")
        ]
        assert genesys_results
        assert all(result.recommendation is None for result in genesys_results)
        assert report.recommendations == ()

    def test_results_are_json_serializable(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        payload = {
            "overall_score": report.overall_score,
            "fail_count": report.fail_count,
            "results": [
                {
                    "rule_id": result.rule_id,
                    "status": result.status.value,
                    "severity": result.severity.value,
                    "category": result.category.value,
                    "message": result.message,
                }
                for result in report.results
                if result.object_type.startswith("genesys_")
            ],
        }
        serialized = json.dumps(payload, sort_keys=True)
        restored = json.loads(serialized)
        assert restored["fail_count"] == report.fail_count

    def test_oauth_failure_severity_is_critical(self) -> None:
        topology = _unhealthy_topology()
        organization = topology.genesys_organizations[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(organization, topology)
            if item.rule_id == "genesys_oauth_failure"
        )
        assert result.severity == HealthSeverity.CRITICAL

    def test_queue_unavailable_severity_is_critical(self) -> None:
        topology = _unhealthy_topology()
        queue = next(obj for obj in topology.genesys_queues if isinstance(obj, Queue))
        result = next(
            item
            for item in HealthEngine().evaluate_object(queue, topology)
            if item.rule_id == "genesys_queue_unavailable"
        )
        assert result.severity == HealthSeverity.CRITICAL

    @pytest.mark.parametrize("rule_id", [rule.id for rule in GENESYS_HEALTH_RULES])
    def test_each_rule_fails_on_unhealthy_topology(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        report = HealthEngine().evaluate_topology(topology)
        matching = [result for result in report.results if result.rule_id == rule_id]
        assert matching
        assert any(result.status == HealthStatus.FAIL for result in matching)
