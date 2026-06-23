"""Tests for AudioCodes SBC health rules."""

from __future__ import annotations

import json

import pytest

from health import HealthCategory, HealthEngine, HealthSeverity, HealthStatus, default_health_rule_registry
from health.audiocodes_rules import AUDIOCODES_HEALTH_RULES
from model.audiocodes_objects import (
    Certificate,
    HACluster,
    IPGroup,
    IPProfile,
    License,
    ManipulationSet,
    MediaRealm,
    MediaSecurityProfile,
    ProxyAddress,
    ProxySet,
    RoutingRule,
    SBCDevice,
    SIPInterface,
    SIPMessagePolicy,
    TLSContext,
)
from topology.topology_builder import TopologyBuilder

_BASE = {
    "vendor": "audiocodes",
    "platform": "Mediant SBC",
    "hostname": "sbc-lab-01.example.com",
    "source_evidence_id": "EVD-ac-health-001",
}


def _prov(parser: str, command: str) -> dict[str, str]:
    return {**_BASE, "source_parser": parser, "source_command": command}


def _healthy_objects() -> list:
    device = SBCDevice.create(
        **_prov("audiocodes_show_voip_status", "show voip status"),
        object_id="VOBJ-ac-device-001",
        device_name="SBC-LAB-01",
        device_status="Active",
    )
    sip_interface = SIPInterface.create(
        **_prov("audiocodes_show_sip_interface", "show sip-interface"),
        object_id="VOBJ-ac-sipif-001",
        name="SIP_TRUNK_1",
        interface_name="SIP_TRUNK_1",
        state="Active",
        transport="TLS",
        tls_context="TLS_CTX_1",
        media_realm="MR_INTERNAL",
    )
    media_realm = MediaRealm.create(
        **_prov("audiocodes_show_media_realm", "show media-realm"),
        object_id="VOBJ-ac-mr-001",
        name="MR_INTERNAL",
        realm_name="MR_INTERNAL",
        state="Active",
        ip_address="10.10.2.10",
        port_range="6000-6499",
    )
    proxy_set = ProxySet.create(
        **_prov("audiocodes_show_proxy_set", "show proxy-set"),
        object_id="VOBJ-ac-ps-001",
        name="PROVIDER_PS",
        proxy_set_name="PROVIDER_PS",
        state="Active",
        enable_heartbeat=True,
    )
    proxy_address = ProxyAddress.create(
        **_prov("audiocodes_show_proxy_set", "show proxy-set"),
        object_id="VOBJ-ac-pa-001",
        name="203.0.113.10",
        proxy_set_name="PROVIDER_PS",
        address="203.0.113.10",
        transport="UDP",
        port=5060,
    )
    ip_group = IPGroup.create(
        **_prov("audiocodes_show_ip_group", "show ip-group"),
        object_id="VOBJ-ac-ig-001",
        name="TO_PROVIDER",
        ip_group_name="TO_PROVIDER",
        state="Active",
        proxy_set="PROVIDER_PS",
        media_realm="MR_INTERNAL",
        ip_profile="DEFAULT_PROFILE",
    )
    ip_profile = IPProfile.create(
        **_prov("audiocodes_show_ip_group", "show ip-group"),
        object_id="VOBJ-ac-ip-001",
        name="DEFAULT_PROFILE",
        profile_name="DEFAULT_PROFILE",
        enable_srtp=True,
        metadata={"peer_srtp_enabled": True},
    )
    routing_rule = RoutingRule.create(
        **_prov("audiocodes_show_routing_table", "show routing-table"),
        object_id="VOBJ-ac-rr-001",
        name="PSTN_OUT",
        rule_name="PSTN_OUT",
        destination="9*",
        ip_group="TO_PROVIDER",
        priority=1,
    )
    manipulation_set = ManipulationSet.create(
        **_prov("audiocodes_show_configuration", "show configuration"),
        object_id="VOBJ-ac-ms-001",
        name="OUTBOUND_HDR",
        set_name="OUTBOUND_HDR",
        state="Active",
    )
    tls_context = TLSContext.create(
        **_prov("audiocodes_show_tls_context", "show tls-context"),
        object_id="VOBJ-ac-tls-001",
        name="TLS_CTX_1",
        context_name="TLS_CTX_1",
        tls_version="TLS1.2",
        certificate_name="SBC_CERT",
    )
    certificate = Certificate.create(
        **_prov("audiocodes_show_certificates", "show certificates"),
        object_id="VOBJ-ac-cert-001",
        name="SBC_CERT",
        certificate_name="SBC_CERT",
        not_after="2027-01-01",
        status="Valid",
    )
    ha_cluster = HACluster.create(
        **_prov("audiocodes_show_ha_status", "show ha-status"),
        object_id="VOBJ-ac-ha-001",
        name="SBC-LAB-01",
        cluster_state="Active",
        active_node="SBC-LAB-01",
        standby_node="SBC-LAB-02",
        sync_state="Synchronized",
    )
    license_obj = License.create(
        **_prov("audiocodes_show_licenses", "show licenses"),
        object_id="VOBJ-ac-lic-001",
        name="Session",
        license_type="Session",
        sessions_total=500,
        sessions_used=120,
        metadata={"license_status": "Valid"},
    )
    sip_policy = SIPMessagePolicy.create(
        **_prov("audiocodes_show_sip_options", "show sip-options"),
        object_id="VOBJ-ac-policy-001",
        name="OPTIONS_KEEPALIVE",
        policy_name="OPTIONS_KEEPALIVE",
        options_enabled=True,
        metadata={"options_status": "Success"},
    )
    media_security = MediaSecurityProfile.create(
        **_prov("audiocodes_show_tls_context", "show tls-context"),
        object_id="VOBJ-ac-msp-001",
        name="SRTP_PROFILE",
        profile_name="SRTP_PROFILE",
        srtp_mode="Enabled",
    )
    return [
        device,
        sip_interface,
        media_realm,
        proxy_set,
        proxy_address,
        ip_group,
        ip_profile,
        routing_rule,
        manipulation_set,
        tls_context,
        certificate,
        ha_cluster,
        license_obj,
        sip_policy,
        media_security,
    ]


def _healthy_topology():
    return TopologyBuilder().build(_healthy_objects())


def _unhealthy_topology():
    objects = _healthy_objects()
    replacements = {
        "VOBJ-ac-device-001": SBCDevice.create(
            **_prov("audiocodes_show_voip_status", "show voip status"),
            object_id="VOBJ-ac-device-001",
            device_name="SBC-LAB-01",
            device_status="Active",
            metadata={"sip_flood_protection": True, "dos_protection": True, "dns_resolution_failure": True},
        ),
        "VOBJ-ac-sipif-001": SIPInterface.create(
            **_prov("audiocodes_show_sip_interface", "show sip-interface"),
            object_id="VOBJ-ac-sipif-001",
            name="SIP_TRUNK_1",
            interface_name="SIP_TRUNK_1",
            state="Down",
            transport="TLS",
            tls_context=None,
            media_realm=None,
            metadata={
                "timeout_408": True,
                "forbidden_403": True,
                "codec_mismatch_488": True,
                "sip_response": "403",
            },
        ),
        "VOBJ-ac-mr-001": MediaRealm.create(
            **_prov("audiocodes_show_media_realm", "show media-realm"),
            object_id="VOBJ-ac-mr-001",
            name="MR_INTERNAL",
            realm_name="MR_INTERNAL",
            state="Down",
            ip_address=None,
            metadata={"rtp_one_way_audio": True},
        ),
        "VOBJ-ac-ps-001": ProxySet.create(
            **_prov("audiocodes_show_proxy_set", "show proxy-set"),
            object_id="VOBJ-ac-ps-001",
            name="PROVIDER_PS",
            proxy_set_name="PROVIDER_PS",
            state="Unavailable",
            metadata={"provider_503": True, "gateway_unreachable": True},
        ),
        "VOBJ-ac-pa-001": ProxyAddress.create(
            **_prov("audiocodes_show_proxy_set", "show proxy-set"),
            object_id="VOBJ-ac-pa-001",
            name="203.0.113.10",
            proxy_set_name="PROVIDER_PS",
            address=None,
            metadata={"gateway_unreachable": True, "dns_resolution_failure": True, "fqdn": "gw.provider.example"},
        ),
        "VOBJ-ac-ig-001": IPGroup.create(
            **_prov("audiocodes_show_ip_group", "show ip-group"),
            object_id="VOBJ-ac-ig-001",
            name="TO_PROVIDER",
            ip_group_name="TO_PROVIDER",
            state="Disabled",
            proxy_set="PROVIDER_PS",
            media_realm=None,
            ip_profile="DEFAULT_PROFILE",
            metadata={"routing_rule_missing": True},
        ),
        "VOBJ-ac-ip-001": IPProfile.create(
            **_prov("audiocodes_show_ip_group", "show ip-group"),
            object_id="VOBJ-ac-ip-001",
            name="DEFAULT_PROFILE",
            profile_name="DEFAULT_PROFILE",
            enable_srtp=False,
            metadata={"peer_srtp_enabled": True, "codec_mismatch_488": True, "srtp_mismatch": True},
        ),
        "VOBJ-ac-rr-001": RoutingRule.create(
            **_prov("audiocodes_show_routing_table", "show routing-table"),
            object_id="VOBJ-ac-rr-001",
            name="PSTN_OUT",
            rule_name="PSTN_OUT",
            destination=None,
            ip_group=None,
            metadata={"routing_rule_missing": True},
        ),
        "VOBJ-ac-ms-001": ManipulationSet.create(
            **_prov("audiocodes_show_configuration", "show configuration"),
            object_id="VOBJ-ac-ms-001",
            name="OUTBOUND_HDR",
            set_name=None,
            state="Inactive",
            metadata={"manipulation_set_missing": True},
        ),
        "VOBJ-ac-tls-001": TLSContext.create(
            **_prov("audiocodes_show_tls_context", "show tls-context"),
            object_id="VOBJ-ac-tls-001",
            name="TLS_CTX_1",
            context_name="TLS_CTX_1",
            metadata={"status": "failed", "tls_negotiation_failure": True},
        ),
        "VOBJ-ac-cert-001": Certificate.create(
            **_prov("audiocodes_show_certificates", "show certificates"),
            object_id="VOBJ-ac-cert-001",
            name="SBC_CERT",
            certificate_name="SBC_CERT",
            status="Expired",
            metadata={"tls_certificate_expired": True},
        ),
        "VOBJ-ac-ha-001": HACluster.create(
            **_prov("audiocodes_show_ha_status", "show ha-status"),
            object_id="VOBJ-ac-ha-001",
            name="SBC-LAB-01",
            cluster_state="Failover",
            sync_state="OutOfSync",
            metadata={"ha_failover": True, "standby_synchronization_failure": True},
        ),
        "VOBJ-ac-lic-001": License.create(
            **_prov("audiocodes_show_licenses", "show licenses"),
            object_id="VOBJ-ac-lic-001",
            name="Session",
            license_type="Session",
            sessions_total=100,
            sessions_used=100,
            metadata={"session_license_exhausted": True, "sbc_license_invalid": True, "license_status": "Invalid"},
        ),
        "VOBJ-ac-policy-001": SIPMessagePolicy.create(
            **_prov("audiocodes_show_sip_options", "show sip-options"),
            object_id="VOBJ-ac-policy-001",
            name="OPTIONS_KEEPALIVE",
            policy_name="OPTIONS_KEEPALIVE",
            options_enabled=False,
            metadata={"sip_options_failure": True, "provider_503": True, "options_status": "503"},
        ),
        "VOBJ-ac-msp-001": MediaSecurityProfile.create(
            **_prov("audiocodes_show_tls_context", "show tls-context"),
            object_id="VOBJ-ac-msp-001",
            name="SRTP_PROFILE",
            profile_name="SRTP_PROFILE",
            srtp_mode="Mismatch",
            metadata={"srtp_mismatch": True},
        ),
    }
    return TopologyBuilder().build([replacements.get(obj.id, obj) for obj in objects])


class TestAudioCodesRuleRegistration:
    def test_default_registry_includes_audiocodes_rules(self) -> None:
        registry = default_health_rule_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert "audiocodes_sip_options_failed" in rule_ids
        assert "audiocodes_gateway_unreachable" in rule_ids
        assert len(AUDIOCODES_HEALTH_RULES) == 25

    @pytest.mark.parametrize("rule", AUDIOCODES_HEALTH_RULES, ids=lambda rule: rule.id)
    def test_every_audiocodes_rule_evaluates(self, rule) -> None:
        topology = _unhealthy_topology()
        target = next(
            obj for obj in topology.all_objects() if obj.object_type in rule.supported_object_types
        )
        result = rule.evaluate(target, topology)
        assert result.rule_id == rule.id
        assert result.status in {HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL}
        assert result.recommendation is None


class TestSipSignalingRules:
    @pytest.mark.parametrize(
        ("rule_id", "object_id"),
        [
            ("audiocodes_sip_options_failed", "VOBJ-ac-policy-001"),
            ("audiocodes_provider_503", "VOBJ-ac-policy-001"),
            ("audiocodes_timeout_408", "VOBJ-ac-sipif-001"),
            ("audiocodes_forbidden_403", "VOBJ-ac-sipif-001"),
            ("audiocodes_codec_mismatch_488", "VOBJ-ac-sipif-001"),
        ],
    )
    def test_rule_fails_on_unhealthy_topology(self, rule_id: str, object_id: str) -> None:
        topology = _unhealthy_topology()
        target = next(obj for obj in topology.all_objects() if obj.id == object_id)
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_sip_options_failed_severity(self) -> None:
        topology = _unhealthy_topology()
        policy = topology.audiocodes_sip_message_policies[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(policy, topology)
            if item.rule_id == "audiocodes_sip_options_failed"
        )
        assert result.severity == HealthSeverity.HIGH


class TestConfigurationRules:
    @pytest.mark.parametrize(
        ("rule_id", "bucket_attr", "index"),
        [
            ("audiocodes_proxy_set_unavailable", "audiocodes_proxy_sets", 0),
            ("audiocodes_ip_group_disabled", "audiocodes_ip_groups", 0),
            ("audiocodes_sip_interface_down", "audiocodes_sip_interfaces", 0),
            ("audiocodes_routing_rule_missing", "audiocodes_routing_rules", 0),
            ("audiocodes_manipulation_set_missing", "audiocodes_manipulation_sets", 0),
        ],
    )
    def test_configuration_rule_fails(self, rule_id: str, bucket_attr: str, index: int) -> None:
        topology = _unhealthy_topology()
        target = getattr(topology, bucket_attr)[index]
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_routing_rule_missing_on_ip_group(self) -> None:
        topology = TopologyBuilder().build(
            [obj for obj in _healthy_objects() if not isinstance(obj, RoutingRule)]
        )
        ip_group = topology.audiocodes_ip_groups[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(ip_group, topology)
            if item.rule_id == "audiocodes_routing_rule_missing"
        )
        assert result.status == HealthStatus.FAIL


class TestTlsSecurityRules:
    @pytest.mark.parametrize(
        ("rule_id", "bucket_attr"),
        [
            ("audiocodes_tls_certificate_expired", "audiocodes_certificates"),
            ("audiocodes_tls_negotiation_failure", "audiocodes_tls_contexts"),
            ("audiocodes_sip_flood_protection", "audiocodes_sbc_devices"),
            ("audiocodes_dos_protection", "audiocodes_sbc_devices"),
        ],
    )
    def test_tls_security_rule_fails(self, rule_id: str, bucket_attr: str) -> None:
        topology = _unhealthy_topology()
        target = getattr(topology, bucket_attr)[0]
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL

    def test_tls_context_missing_fails(self) -> None:
        topology = _unhealthy_topology()
        sip_interface = topology.audiocodes_sip_interfaces[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(sip_interface, topology)
            if item.rule_id == "audiocodes_tls_context_missing"
        )
        assert result.status == HealthStatus.FAIL
        assert result.category == HealthCategory.TLS


class TestMediaRules:
    @pytest.mark.parametrize(
        ("rule_id", "bucket_attr"),
        [
            ("audiocodes_media_realm_missing", "audiocodes_ip_groups"),
            ("audiocodes_media_realm_down", "audiocodes_media_realms"),
            ("audiocodes_rtp_one_way_audio", "audiocodes_media_realms"),
            ("audiocodes_srtp_mismatch", "audiocodes_media_security_profiles"),
        ],
    )
    def test_media_rule_fails(self, rule_id: str, bucket_attr: str) -> None:
        topology = _unhealthy_topology()
        target = getattr(topology, bucket_attr)[0]
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL
        assert result.category == HealthCategory.MEDIA


class TestHaLicensingRules:
    @pytest.mark.parametrize(
        ("rule_id",),
        [
            ("audiocodes_standby_synchronization_failure",),
            ("audiocodes_ha_failover",),
            ("audiocodes_session_license_exhausted",),
            ("audiocodes_sbc_license_invalid",),
        ],
    )
    def test_ha_licensing_rule_fails(self, rule_id: str) -> None:
        topology = _unhealthy_topology()
        if rule_id in {"audiocodes_session_license_exhausted", "audiocodes_sbc_license_invalid"}:
            target = topology.audiocodes_licenses[0]
        else:
            target = topology.audiocodes_ha_clusters[0]
        result = next(
            item for item in HealthEngine().evaluate_object(target, topology) if item.rule_id == rule_id
        )
        assert result.status == HealthStatus.FAIL


class TestNetworkRules:
    def test_gateway_unreachable_on_proxy_address(self) -> None:
        topology = _unhealthy_topology()
        address = topology.audiocodes_proxy_addresses[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(address, topology)
            if item.rule_id == "audiocodes_gateway_unreachable"
        )
        assert result.status == HealthStatus.FAIL
        assert result.category == HealthCategory.NETWORK

    def test_dns_resolution_failure_on_device(self) -> None:
        topology = _unhealthy_topology()
        device = topology.audiocodes_sbc_devices[0]
        result = next(
            item
            for item in HealthEngine().evaluate_object(device, topology)
            if item.rule_id == "audiocodes_dns_resolution_failure"
        )
        assert result.status == HealthStatus.FAIL


class TestHealthyTopology:
    def test_healthy_topology_has_no_audiocodes_failures(self) -> None:
        report = HealthEngine().evaluate_topology(_healthy_topology())
        audiocodes_results = [
            result
            for result in report.results
            if result.object_type.startswith("audiocodes_")
        ]
        assert audiocodes_results
        assert all(result.status == HealthStatus.PASS for result in audiocodes_results)

    def test_healthy_sbc_device_passes_security_rules(self) -> None:
        topology = _healthy_topology()
        device = topology.audiocodes_sbc_devices[0]
        results = {
            item.rule_id: item
            for item in HealthEngine().evaluate_object(device, topology)
            if item.rule_id in {
                "audiocodes_sip_flood_protection",
                "audiocodes_dos_protection",
                "audiocodes_dns_resolution_failure",
            }
        }
        assert all(result.status == HealthStatus.PASS for result in results.values())


class TestHealthEngineIntegration:
    def test_multiple_simultaneous_failures_reduce_score(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        failures = [
            result
            for result in report.results
            if result.object_type.startswith("audiocodes_") and result.status == HealthStatus.FAIL
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

    def test_audiocodes_results_have_no_recommendations(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        audiocodes_results = [
            result for result in report.results if result.object_type.startswith("audiocodes_")
        ]
        assert audiocodes_results
        assert all(result.recommendation is None for result in audiocodes_results)

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
                if result.object_type.startswith("audiocodes_")
            ],
        }
        serialized = json.dumps(payload, sort_keys=True)
        restored = json.loads(serialized)
        assert restored["fail_count"] == report.fail_count
