"""Tests for the deterministic health rule framework."""

from __future__ import annotations

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from health import (
    DuplicateHealthRuleError,
    HealthCategory,
    HealthEngine,
    HealthRuleRegistry,
    HealthSeverity,
    HealthStatus,
    default_health_rule_registry,
)
from health.builtin_rules import BUILTIN_HEALTH_RULES, ProviderNoDependentDialPeersRule
from health.health_rule import HealthRule
from model import DialPeer, Provider, SipUA, VoiceService
from topology.topology_builder import TopologyBuilder


def _provenance(**overrides: str) -> dict[str, str]:
    base = {
        "vendor": "cisco",
        "platform": "CUBE",
        "hostname": "cube-edge-01",
        "source_parser": "cisco_show_sip_ua_status",
        "source_command": "show sip-ua status",
        "source_evidence_id": "EVD-test-001",
    }
    base.update(overrides)
    return base


def _healthy_topology():
    sip_ua = SipUA.create(**_provenance(), enabled=True, object_id="VOBJ-sip-ua-001")
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        allow_connections=True,
        object_id="VOBJ-voice-service-001",
    )
    dial_peer = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        destination_pattern="9T",
        session_target="ipv4:192.0.2.10",
        shutdown=False,
        object_id="VOBJ-dial-peer-001",
    )
    provider = Provider.create(
        **_provenance(),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-001",
    )
    return TopologyBuilder().build([dial_peer, voice_service, sip_ua, provider])


def _unhealthy_topology():
    sip_ua = SipUA.create(**_provenance(), enabled=False, object_id="VOBJ-sip-ua-001")
    voice_service = VoiceService.create(
        **_provenance(
            source_parser="cisco_show_run_voice_service_voip",
            source_command="show run | sec voice service voip",
        ),
        allow_connections=None,
        object_id="VOBJ-voice-service-001",
    )
    dial_peer = DialPeer.create(
        **_provenance(
            source_parser="cisco_show_dial_peer_voice_summary",
            source_command="show dial-peer voice summary",
        ),
        tag=1,
        destination_pattern="",
        shutdown=True,
        session_target="ipv4:192.0.2.10",
        object_id="VOBJ-dial-peer-001",
    )
    provider_a = Provider.create(
        **_provenance(),
        name="ITSP-Primary",
        addresses=("ipv4:192.0.2.10",),
        object_id="VOBJ-provider-a",
    )
    provider_b = Provider.create(
        **_provenance(),
        name="ITSP-Orphan",
        addresses=("ipv4:203.0.113.10",),
        object_id="VOBJ-provider-b",
    )
    return TopologyBuilder().build([dial_peer, voice_service, sip_ua, provider_a, provider_b])


class TestBuiltInRules:
    @pytest.mark.parametrize("rule", BUILTIN_HEALTH_RULES, ids=lambda rule: rule.id)
    def test_every_builtin_rule_evaluates(self, rule: HealthRule) -> None:
        topology = _unhealthy_topology()
        target = next(obj for obj in topology.all_objects() if obj.object_type in rule.supported_object_types)
        result = rule.evaluate(target, topology)

        assert result.rule_id == rule.id
        assert result.object_id == target.id
        assert result.status in {HealthStatus.PASS, HealthStatus.WARN, HealthStatus.FAIL}

    def test_sip_ua_disabled_rule_fails(self) -> None:
        topology = _unhealthy_topology()
        sip_ua = topology.sip_uas[0]
        disabled = next(
            result
            for result in HealthEngine().evaluate_object(sip_ua, topology)
            if result.rule_id == "sip_ua_disabled"
        )

        assert disabled.status == HealthStatus.FAIL
        assert disabled.category == HealthCategory.SIP
        assert disabled.severity == HealthSeverity.CRITICAL

    def test_voice_service_allow_connections_missing_warns(self) -> None:
        topology = _unhealthy_topology()
        voice_service = topology.voice_services[0]
        result = next(
            result
            for result in HealthEngine().evaluate_object(voice_service, topology)
            if result.rule_id == "voice_service_allow_connections_missing"
        )

        assert result.status == HealthStatus.WARN
        assert result.category == HealthCategory.CONFIGURATION

    def test_dial_peer_rules_fail(self) -> None:
        topology = _unhealthy_topology()
        dial_peer = topology.dial_peers[0]
        results = {
            result.rule_id: result for result in HealthEngine().evaluate_object(dial_peer, topology)
        }

        assert results["dial_peer_no_destination_pattern"].status == HealthStatus.FAIL
        assert results["dial_peer_shutdown"].status == HealthStatus.FAIL

    def test_provider_no_dependent_dial_peers_warns(self) -> None:
        topology = _unhealthy_topology()
        orphan_provider = next(provider for provider in topology.providers if provider.id == "VOBJ-provider-b")
        result = ProviderNoDependentDialPeersRule().evaluate(orphan_provider, topology)

        assert result.status == HealthStatus.WARN
        assert result.category == HealthCategory.PROVIDER


class TestHealthEngine:
    def test_score_calculation(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())

        assert report.overall_score == 25
        assert report.fail_count == 3
        assert report.warn_count == 2

    def test_category_aggregation(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        categories = dict(report.category_counts)

        assert categories[HealthCategory.SIP] == 1
        assert categories[HealthCategory.CONFIGURATION] == 1
        assert categories[HealthCategory.DIAL_PLAN] == 1
        assert categories[HealthCategory.ROUTING] == 1
        assert categories[HealthCategory.PROVIDER] == 1

    def test_severity_aggregation(self) -> None:
        report = HealthEngine().evaluate_topology(_unhealthy_topology())
        severities = dict(report.severity_counts)

        assert severities["critical"] == 1
        assert severities["medium"] == 1
        assert severities["high"] == 2
        assert severities["low"] == 1

    def test_topology_evaluation_on_healthy_graph(self) -> None:
        report = HealthEngine().evaluate_topology(_healthy_topology())

        assert report.overall_score == 100
        assert report.fail_count == 0
        assert report.warn_count == 0
        assert report.pass_count == len(BUILTIN_HEALTH_RULES)

    def test_case_evaluation(self) -> None:
        topology = _unhealthy_topology()
        case = Case(
            case_id="CASE-HEALTH-001",
            title="health test",
            status=InvestigationState.ANALYSIS,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="outbound calls fail"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
            voice_objects=list(topology.all_objects()),
        )

        report = HealthEngine().evaluate_case(case)

        assert report.fail_count == 3
        assert report.recommendations
        assert "Enable SIP-UA and validate registration." in report.recommendations

    def test_deterministic_ordering(self) -> None:
        engine = HealthEngine()
        topology = _unhealthy_topology()

        first = engine.evaluate_topology(topology)
        second = engine.evaluate_topology(topology)

        assert first.results == second.results
        assert [result.rule_id for result in first.results] == sorted(
            result.rule_id for result in first.results
        )


class TestHealthRuleRegistry:
    def test_default_registry_contains_builtin_rules(self) -> None:
        registry = default_health_rule_registry()

        assert len(registry.all_rules()) == len(BUILTIN_HEALTH_RULES)
        assert registry.get("sip_ua_disabled") is not None

    def test_lookup_by_object_type(self) -> None:
        registry = default_health_rule_registry()
        dial_peer_rules = registry.rules_for_object_type("dial_peer")

        assert [rule.id for rule in dial_peer_rules] == [
            "dial_peer_no_destination_pattern",
            "dial_peer_shutdown",
        ]

    def test_prevent_duplicate_rule_ids(self) -> None:
        registry = HealthRuleRegistry()
        registry.register(BUILTIN_HEALTH_RULES[0])

        with pytest.raises(DuplicateHealthRuleError):
            registry.register(BUILTIN_HEALTH_RULES[0])
