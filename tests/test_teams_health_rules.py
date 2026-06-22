"""Tests for Microsoft Teams health rules."""

from __future__ import annotations

import json

import pytest

from health import HealthCategory, HealthEngine, HealthSeverity, HealthStatus, default_health_rule_registry
from health.teams_rules import TEAMS_HEALTH_RULES
from model.teams_objects import (
    TeamsAutoAttendant,
    TeamsCallQueue,
    TeamsLisLocation,
    TeamsPhoneNumber,
    TeamsPstnGateway,
    TeamsResourceAccount,
    TeamsUser,
    TeamsVoiceRoute,
    TeamsVoiceRoutingPolicy,
)
from topology.topology_builder import TopologyBuilder

_BASE = {
    "vendor": "microsoft",
    "platform": "Teams Phone",
    "hostname": "contoso.onmicrosoft.com",
    "source_evidence_id": "EVD-teams-health-001",
}


def _prov(parser: str, command: str) -> dict[str, str]:
    return {**_BASE, "source_parser": parser, "source_command": command}


def _user(**overrides) -> TeamsUser:
    metadata = {
        "teams_phone_license_assigned": True,
        "calling_plan_license_assigned": True,
        "caller_id_policy": "Contoso-CallerID",
        "location_policy": "US-Location",
        "emergency_calling_policy": "US-Emergency",
        "emergency_routing_policy": "US-Emergency-Route",
    }
    metadata.update(overrides.pop("metadata", {}))
    fields = {
        "object_id": "VOBJ-teams-user-001",
        "user_principal_name": "user@contoso.com",
        "enterprise_voice_enabled": True,
        "line_uri": "tel:+15551234567",
        "voice_routing_policy": "US-International",
        "dial_plan": "ContosoDialPlan",
    }
    fields.update(overrides)
    return TeamsUser.create(
        **_prov("microsoft_get_csonlineuser", "get-csonlineuser"),
        metadata=metadata,
        **fields,
    )


def _healthy_topology():
    user = _user()
    policy = TeamsVoiceRoutingPolicy.create(
        **_BASE,
        object_id="VOBJ-teams-policy-001",
        name="US-International",
        pstn_usages=("International",),
        source_parser="microsoft_get_csonlinevoiceroutingpolicy",
        source_command="get-csonlinevoiceroutingpolicy",
    )
    route = TeamsVoiceRoute.create(
        **_BASE,
        object_id="VOBJ-teams-route-001",
        name="US-Route",
        online_pstn_usages=("International",),
        online_pstn_gateway_list=("sbc.contoso.com",),
        source_parser="microsoft_get_csonlinevoiceroute",
        source_command="get-csonlinevoiceroute",
    )
    gateway = TeamsPstnGateway.create(
        **_BASE,
        object_id="VOBJ-teams-gateway-001",
        name="sbc.contoso.com",
        fqdn="sbc.contoso.com",
        enabled=True,
        source_parser="microsoft_get_csonlinepstngateway",
        source_command="get-csonlinepstngateway",
        metadata={"trusted_ips": "10.0.0.0/8", "media_bypass_enabled": True},
    )
    resource = TeamsResourceAccount.create(
        **_BASE,
        object_id="VOBJ-teams-resource-001",
        name="aa-resource@contoso.com",
        phone_number="tel:+15559876543",
        application_type="AutoAttendant",
        source_parser="microsoft_get_csresourceaccount",
        source_command="get-csresourceaccount",
        metadata={"license_assigned": True},
    )
    attendant = TeamsAutoAttendant.create(
        **_BASE,
        object_id="VOBJ-teams-aa-001",
        name="Main-AA",
        operator="aa-resource@contoso.com",
        source_parser="microsoft_get_csautoattendant",
        source_command="get-csautoattendant",
        metadata={"resource_account": "aa-resource@contoso.com"},
    )
    queue = TeamsCallQueue.create(
        **_BASE,
        object_id="VOBJ-teams-cq-001",
        name="Support-Queue",
        source_parser="microsoft_get_cscallqueue",
        source_command="get-cscallqueue",
        metadata={"resource_account": "aa-resource@contoso.com"},
    )
    lis = TeamsLisLocation.create(
        **_BASE,
        object_id="VOBJ-teams-lis-001",
        name="HQ-Floor-1",
        civic_address="123 Main St",
        location="Floor 1",
        e911_enabled=True,
        source_parser="microsoft_get_csonlinelislocation",
        source_command="get-csonlinelislocation",
    )
    phone_number = TeamsPhoneNumber.create(
        **_BASE,
        object_id="VOBJ-teams-number-001",
        telephone_number="+15551112222",
        assigned_purpose="OperatorConnect",
        assignment_status="Assigned",
        assigned_to="user@contoso.com",
        source_parser="microsoft_get_csphonenumberassignment",
        source_command="get-csphonenumberassignment",
        metadata={"operator_connect_provider": "ContosoTelco"},
    )
    return TopologyBuilder().build(
        [user, policy, route, gateway, resource, attendant, queue, lis, phone_number]
    )


def _unhealthy_topology():
    user = _user(
        object_id="VOBJ-teams-user-bad",
        enterprise_voice_enabled=False,
        line_uri=None,
        voice_routing_policy=None,
        dial_plan=None,
        metadata={
            "teams_phone_license_missing": True,
            "calling_plan_license_missing": True,
            "caller_id_policy_missing": True,
            "location_policy_missing": True,
            "emergency_calling_policy_missing": True,
            "emergency_routing_policy_missing": True,
        },
    )
    policy = TeamsVoiceRoutingPolicy.create(
        **_BASE,
        object_id="VOBJ-teams-policy-bad",
        name="Empty-Policy",
        pstn_usages=("International",),
        source_parser="microsoft_get_csonlinevoiceroutingpolicy",
        source_command="get-csonlinevoiceroutingpolicy",
    )
    route = TeamsVoiceRoute.create(
        **_BASE,
        object_id="VOBJ-teams-route-bad",
        name="No-Gateway-Route",
        online_pstn_usages=("MissingUsage",),
        online_pstn_gateway_list=(),
        source_parser="microsoft_get_csonlinevoiceroute",
        source_command="get-csonlinevoiceroute",
    )
    gateway = TeamsPstnGateway.create(
        **_BASE,
        object_id="VOBJ-teams-gateway-bad",
        name="orphan-sbc.contoso.com",
        fqdn="orphan-sbc.contoso.com",
        enabled=False,
        source_parser="microsoft_get_csonlinepstngateway",
        source_command="get-csonlinepstngateway",
        metadata={
            "tls_certificate_expired": True,
            "sip_options_failed": True,
            "media_bypass_disabled": True,
            "trusted_ip_missing": True,
        },
    )
    resource = TeamsResourceAccount.create(
        **_BASE,
        object_id="VOBJ-teams-resource-bad",
        name="unlicensed-resource@contoso.com",
        phone_number=None,
        source_parser="microsoft_get_csresourceaccount",
        source_command="get-csresourceaccount",
        metadata={"resource_account_license_missing": True, "license_assigned": False},
    )
    attendant = TeamsAutoAttendant.create(
        **_BASE,
        object_id="VOBJ-teams-aa-bad",
        name="Broken-AA",
        source_parser="microsoft_get_csautoattendant",
        source_command="get-csautoattendant",
    )
    queue = TeamsCallQueue.create(
        **_BASE,
        object_id="VOBJ-teams-cq-bad",
        name="Broken-Queue",
        source_parser="microsoft_get_cscallqueue",
        source_command="get-cscallqueue",
    )
    lis = TeamsLisLocation.create(
        **_BASE,
        object_id="VOBJ-teams-lis-bad",
        name="Empty-LIS",
        civic_address=None,
        location=None,
        e911_enabled=False,
        source_parser="microsoft_get_csonlinelislocation",
        source_command="get-csonlinelislocation",
    )
    phone_number = TeamsPhoneNumber.create(
        **_BASE,
        object_id="VOBJ-teams-number-bad",
        telephone_number="+15553334444",
        assigned_purpose="OperatorConnect",
        assignment_status="Unassigned",
        assigned_to=None,
        source_parser="microsoft_get_csphonenumberassignment",
        source_command="get-csphonenumberassignment",
        metadata={"operator_connect_provider_missing": True},
    )
    return TopologyBuilder().build(
        [user, policy, route, gateway, resource, attendant, queue, lis, phone_number]
    )


class TestTeamsRuleRegistration:
    def test_default_registry_includes_teams_rules(self) -> None:
        registry = default_health_rule_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert "teams_phone_license_missing" in rule_ids
        assert "enterprise_voice_disabled" in rule_ids
        assert len(TEAMS_HEALTH_RULES) == 26

    @pytest.mark.parametrize("rule", TEAMS_HEALTH_RULES, ids=lambda rule: rule.id)
    def test_every_teams_rule_evaluates(self, rule) -> None:
        topology = _unhealthy_topology()
        target = next(
            obj for obj in topology.all_objects() if obj.object_type in rule.supported_object_types
        )
        result = rule.evaluate(target, topology)
        assert result.rule_id == rule.id
        assert result.status in {HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL}
        assert result.recommendation is None


class TestLicensingRules:
    def test_teams_phone_license_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "teams_phone_license_missing"
        )
        assert result.status == HealthStatus.FAIL
        assert result.severity == HealthSeverity.HIGH

    def test_enterprise_voice_disabled_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "enterprise_voice_disabled"
        )
        assert result.status == HealthStatus.FAIL

    def test_calling_plan_license_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "calling_plan_license_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_resource_account_license_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        account = topology.teams_resource_accounts[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(account, topology)
            if item.rule_id == "resource_account_license_missing"
        )
        assert result.status == HealthStatus.FAIL


class TestUserConfigurationRules:
    def test_phone_number_not_assigned_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "phone_number_not_assigned"
        )
        assert result.status == HealthStatus.FAIL

    def test_voice_routing_policy_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "voice_routing_policy_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_tenant_dial_plan_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "tenant_dial_plan_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_caller_id_policy_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "caller_id_policy_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_location_policy_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "location_policy_missing"
        )
        assert result.status == HealthStatus.FAIL


class TestVoiceRoutingRules:
    def test_pstn_usage_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        policy = TeamsVoiceRoutingPolicy.create(
            **_BASE,
            object_id="VOBJ-teams-policy-empty-usage",
            name="No-Usage-Policy",
            pstn_usages=(),
            source_parser="microsoft_get_csonlinevoiceroutingpolicy",
            source_command="get-csonlinevoiceroutingpolicy",
        )
        objects = [obj for obj in topology.all_objects() if obj.id != "VOBJ-teams-policy-bad"]
        objects.append(policy)
        topology = TopologyBuilder().build(objects)
        result = next(
            item
            for item in HealthEngine().evaluate_object(policy, topology)
            if item.rule_id == "pstn_usage_missing"
        )
        assert result.status == HealthStatus.FAIL
        assert result.category == HealthCategory.ROUTING

    def test_voice_route_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        policy = topology.teams_voice_routing_policies[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(policy, topology)
            if item.rule_id == "voice_route_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_voice_route_without_gateway_fails(self) -> None:
        topology = _unhealthy_topology()
        route = topology.teams_voice_routes[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(route, topology)
            if item.rule_id == "voice_route_without_gateway"
        )
        assert result.status == HealthStatus.FAIL
        assert result.severity == HealthSeverity.CRITICAL

    def test_gateway_not_referenced_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "gateway_not_referenced"
        )
        assert result.status == HealthStatus.FAIL


class TestDirectRoutingRules:
    def test_sbc_unreachable_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "sbc_unreachable"
        )
        assert result.status == HealthStatus.FAIL
        assert result.severity == HealthSeverity.CRITICAL

    def test_tls_certificate_expired_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "tls_certificate_expired"
        )
        assert result.status == HealthStatus.FAIL

    def test_sip_options_failed_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "sip_options_failed"
        )
        assert result.status == HealthStatus.FAIL

    def test_media_bypass_disabled_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "media_bypass_disabled"
        )
        assert result.status == HealthStatus.FAIL
        assert result.category == HealthCategory.MEDIA


class TestOperatorConnectRules:
    def test_operator_connect_provider_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        number = topology.teams_phone_numbers[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(number, topology)
            if item.rule_id == "operator_connect_provider_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_operator_connect_number_unassigned_fails(self) -> None:
        topology = _unhealthy_topology()
        number = topology.teams_phone_numbers[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(number, topology)
            if item.rule_id == "operator_connect_number_unassigned"
        )
        assert result.status == HealthStatus.FAIL


class TestEmergencyCallingRules:
    def test_emergency_calling_policy_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "emergency_calling_policy_missing"
        )
        assert result.status == HealthStatus.FAIL
        assert result.severity == HealthSeverity.CRITICAL

    def test_emergency_routing_policy_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        user = topology.teams_users[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id == "emergency_routing_policy_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_lis_location_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        location = topology.teams_lis_locations[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(location, topology)
            if item.rule_id == "lis_location_missing"
        )
        assert result.status == HealthStatus.FAIL

    def test_trusted_ip_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        gateway = topology.teams_pstn_gateways[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(gateway, topology)
            if item.rule_id == "trusted_ip_missing"
        )
        assert result.status == HealthStatus.FAIL


class TestResourceAccountRules:
    def test_auto_attendant_missing_resource_account_fails(self) -> None:
        topology = _unhealthy_topology()
        attendant = topology.teams_auto_attendants[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(attendant, topology)
            if item.rule_id == "auto_attendant_missing_resource_account"
        )
        assert result.status == HealthStatus.FAIL

    def test_call_queue_missing_resource_account_fails(self) -> None:
        topology = _unhealthy_topology()
        queue = topology.teams_call_queues[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(queue, topology)
            if item.rule_id == "call_queue_missing_resource_account"
        )
        assert result.status == HealthStatus.FAIL

    def test_resource_account_unlicensed_fails(self) -> None:
        topology = _unhealthy_topology()
        account = topology.teams_resource_accounts[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(account, topology)
            if item.rule_id == "resource_account_unlicensed"
        )
        assert result.status == HealthStatus.FAIL


class TestHealthyTopology:
    def test_healthy_user_passes_configuration_rules(self) -> None:
        topology = _healthy_topology()
        user = topology.teams_users[0]
        results = {
            item.rule_id: item
            for item in HealthEngine().evaluate_object(user, topology)
            if item.rule_id.startswith(
                (
                    "teams_phone",
                    "enterprise_voice",
                    "calling_plan",
                    "phone_number",
                    "voice_routing_policy",
                    "tenant_dial_plan",
                    "caller_id",
                    "location_policy",
                    "emergency",
                )
            )
        }
        assert all(result.status == HealthStatus.PASS for result in results.values())

    def test_healthy_topology_has_no_teams_failures(self) -> None:
        report = HealthEngine().evaluate_topology(_healthy_topology())
        teams_results = [
            result
            for result in report.results
            if result.object_type.startswith("teams_")
        ]
        assert teams_results
        assert all(result.status == HealthStatus.PASS for result in teams_results)


class TestHealthEngineIntegration:
    def test_multiple_simultaneous_failures_reduce_score(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        teams_failures = [
            result
            for result in report.results
            if result.object_type.startswith("teams_") and result.status == HealthStatus.FAIL
        ]
        assert len(teams_failures) >= 20
        assert report.overall_score < 50
        assert report.fail_count >= 20

    def test_severity_ordering_in_aggregation(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        severities = dict(report.severity_counts)
        assert severities.get("critical", 0) >= 3
        assert severities.get("high", 0) >= 10

    def test_deterministic_result_ordering(self) -> None:
        engine = HealthEngine()
        topology = _unhealthy_topology()
        first = engine.evaluate_topology(topology)
        second = engine.evaluate_topology(topology)
        assert first.results == second.results

    def test_teams_results_have_no_recommendations(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        teams_results = [
            result for result in report.results if result.object_type.startswith("teams_")
        ]
        assert teams_results
        assert all(result.recommendation is None for result in teams_results)
        assert not any(
            recommendation
            for recommendation in report.recommendations
            if any(rule.id in recommendation for rule in TEAMS_HEALTH_RULES)
        )

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
                if result.object_type.startswith("teams_")
            ],
        }
        serialized = json.dumps(payload, sort_keys=True)
        restored = json.loads(serialized)
        assert restored["fail_count"] == report.fail_count
