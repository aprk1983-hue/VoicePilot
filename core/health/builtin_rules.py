"""Built-in vendor-neutral health rules for CVOM v1."""

from __future__ import annotations

from dataclasses import dataclass

from health.health_categories import HealthCategory
from health.health_models import HealthResult, HealthStatus
from health.health_rule import HealthRule
from health.health_severity import HealthSeverity
from model.dial_peer import DialPeer
from model.provider import Provider
from model.sip_ua import SipUA
from model.voice_graph import OBJECT_TYPE_DIAL_PEER, OBJECT_TYPE_PROVIDER, OBJECT_TYPE_SIP_UA, OBJECT_TYPE_VOICE_SERVICE, VoiceObject
from model.voice_service import VoiceService
from model.voice_topology import VoiceTopology
from topology.dependency_engine import DependencyEngine
from topology.relationship_types import RelationshipType


@dataclass(frozen=True)
class SipUaDisabledRule(HealthRule):
    id: str = "sip_ua_disabled"
    title: str = "SIP-UA disabled"
    description: str = "SIP user agent must be enabled for SIP call processing."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_SIP_UA,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        sip_ua = _require_type(obj, SipUA)
        if sip_ua.enabled is False:
            return _result(
                rule=self,
                obj=sip_ua,
                status=HealthStatus.FAIL,
                message="SIP-UA is disabled.",
                recommendation="Enable SIP-UA and validate registration.",
            )
        return _pass_result(self, sip_ua, "SIP-UA is enabled or state is unknown.")


@dataclass(frozen=True)
class VoiceServiceAllowConnectionsMissingRule(HealthRule):
    id: str = "voice_service_allow_connections_missing"
    title: str = "Voice service allow-connections missing"
    description: str = "Voice service should declare allow-connections policy."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_VOICE_SERVICE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        voice_service = _require_type(obj, VoiceService)
        if voice_service.allow_connections is None:
            return _result(
                rule=self,
                obj=voice_service,
                status=HealthStatus.WARN,
                message="allow-connections policy is missing from voice service configuration.",
                recommendation="Review voice service voip allow-connections settings.",
            )
        return _pass_result(
            self,
            voice_service,
            "Voice service allow-connections policy is present.",
        )


@dataclass(frozen=True)
class DialPeerNoDestinationPatternRule(HealthRule):
    id: str = "dial_peer_no_destination_pattern"
    title: str = "Dial peer missing destination pattern"
    description: str = "Dial peers require a destination pattern for routing."
    category: HealthCategory = HealthCategory.DIAL_PLAN
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_DIAL_PEER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        dial_peer = _require_type(obj, DialPeer)
        if not (dial_peer.destination_pattern or "").strip():
            return _result(
                rule=self,
                obj=dial_peer,
                status=HealthStatus.FAIL,
                message="Dial peer has no destination pattern.",
                recommendation="Configure destination-pattern on the dial peer.",
            )
        return _pass_result(self, dial_peer, "Dial peer destination pattern is present.")


@dataclass(frozen=True)
class DialPeerShutdownRule(HealthRule):
    id: str = "dial_peer_shutdown"
    title: str = "Dial peer shutdown"
    description: str = "Shutdown dial peers cannot process calls."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_DIAL_PEER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        dial_peer = _require_type(obj, DialPeer)
        if dial_peer.shutdown is True:
            return _result(
                rule=self,
                obj=dial_peer,
                status=HealthStatus.FAIL,
                message="Dial peer is administratively shutdown.",
                recommendation="Remove shutdown and verify dial peer status.",
            )
        return _pass_result(self, dial_peer, "Dial peer is not shutdown.")


@dataclass(frozen=True)
class ProviderNoDependentDialPeersRule(HealthRule):
    id: str = "provider_no_dependent_dial_peers"
    title: str = "Provider has no dependent dial peers"
    description: str = "Providers should be referenced by at least one outbound dial peer."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.LOW
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_PROVIDER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        provider = _require_type(obj, Provider)
        dial_peer_dependents = _dial_peer_routes_to_provider(topology, provider.id)
        if not dial_peer_dependents:
            return _result(
                rule=self,
                obj=provider,
                status=HealthStatus.WARN,
                message="No dial peers route to this provider.",
                recommendation="Verify provider trunk references and dial-peer session targets.",
            )
        return _pass_result(
            self,
            provider,
            f"{len(dial_peer_dependents)} dial peer(s) route to this provider.",
        )


BUILTIN_HEALTH_RULES: tuple[HealthRule, ...] = (
    SipUaDisabledRule(),
    VoiceServiceAllowConnectionsMissingRule(),
    DialPeerNoDestinationPatternRule(),
    DialPeerShutdownRule(),
    ProviderNoDependentDialPeersRule(),
)


def register_builtin_rules(registry) -> None:
    """Register all built-in health rules."""
    for rule in BUILTIN_HEALTH_RULES:
        registry.register(rule)
    from health.cucm_rules import register_cucm_health_rules

    register_cucm_health_rules(registry)


def _dial_peer_routes_to_provider(topology: VoiceTopology, provider_id: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                relationship.source_object_id
                for relationship in topology.relationships
                if (
                    relationship.target_object_id == provider_id
                    and relationship.relationship_type == RelationshipType.ROUTES_TO.value
                )
            }
        )
    )


def _require_type(obj: VoiceObject, expected_type: type):
    if not isinstance(obj, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(obj).__name__}")
    return obj


def _result(
    *,
    rule: HealthRule,
    obj: VoiceObject,
    status: HealthStatus,
    message: str,
    recommendation: str | None,
) -> HealthResult:
    return HealthResult(
        rule_id=rule.id,
        title=rule.title,
        description=rule.description,
        category=rule.category,
        severity=rule.severity,
        status=status,
        object_id=obj.id,
        object_type=obj.object_type,
        message=message,
        recommendation=recommendation,
    )


def _pass_result(rule: HealthRule, obj: VoiceObject, message: str) -> HealthResult:
    return _result(
        rule=rule,
        obj=obj,
        status=HealthStatus.PASS,
        message=message,
        recommendation=None,
    )
