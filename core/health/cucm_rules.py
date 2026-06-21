"""Cisco CUCM health rules for CVOM."""

from __future__ import annotations

from dataclasses import dataclass

from health.health_categories import HealthCategory
from health.health_models import HealthResult, HealthStatus
from health.health_rule import HealthRule
from health.health_severity import HealthSeverity
from model.cucm_objects import CUCMNode, Phone, SIPTrunk
from model.voice_graph import OBJECT_TYPE_CUCM_NODE, OBJECT_TYPE_PHONE, OBJECT_TYPE_SIP_TRUNK, VoiceObject
from model.voice_topology import VoiceTopology


@dataclass(frozen=True)
class PhoneNotRegisteredRule(HealthRule):
    id: str = "phone_not_registered"
    title: str = "Phone not registered"
    description: str = "Phones should be registered to a CUCM node."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_PHONE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        phone = _require_type(obj, Phone)
        if phone.registered is False:
            return _fail(self, phone, "Phone is not registered.", "Restore registration per phone registration runbook.")
        return _pass(self, phone, "Phone is registered or state unknown.")


@dataclass(frozen=True)
class DbReplicationUnhealthyRule(HealthRule):
    id: str = "db_replication_unhealthy"
    title: str = "DB replication unhealthy"
    description: str = "CUCM database replication should be healthy."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        metadata = node.metadata or {}
        if metadata.get("replication_healthy") is False:
            return _fail(self, node, "Database replication is unhealthy.", "Follow cluster replication runbook.")
        return _pass(self, node, "Database replication state not reported as unhealthy.")


@dataclass(frozen=True)
class CallManagerServiceStoppedRule(HealthRule):
    id: str = "callmanager_service_stopped"
    title: str = "CallManager service stopped"
    description: str = "Cisco CallManager service must be running."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.service_state == "stopped":
            return _fail(self, node, "CallManager service is stopped.", "Restart Cisco CallManager service.")
        return _pass(self, node, "CallManager service is running or unknown.")


@dataclass(frozen=True)
class TftpServiceStoppedRule(HealthRule):
    id: str = "tftp_service_stopped"
    title: str = "TFTP service stopped"
    description: str = "Cisco TFTP service must be running for phone config delivery."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        metadata = node.metadata or {}
        if metadata.get("tftp_stopped"):
            return _fail(self, node, "TFTP service is stopped.", "Start Cisco TFTP service.")
        return _pass(self, node, "TFTP service is running or unknown.")


@dataclass(frozen=True)
class CertificateExpiredRule(HealthRule):
    id: str = "certificate_expired"
    title: str = "Certificate expired"
    description: str = "CUCM certificates must be valid."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.metadata.get("certificate_expired"):
            return _fail(self, node, "Certificate is expired.", "Renew Tomcat certificate.")
        return _pass(self, node, "Certificate state not reported as expired.")


@dataclass(frozen=True)
class SipTrunkDownRule(HealthRule):
    id: str = "sip_trunk_down"
    title: str = "SIP trunk down"
    description: str = "SIP trunks should be in service."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_SIP_TRUNK,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        trunk = _require_type(obj, SIPTrunk)
        if (trunk.status or "").lower() == "down":
            return _fail(self, trunk, "SIP trunk is down.", "Restore SIP trunk connectivity.")
        return _pass(self, trunk, "SIP trunk is up or state unknown.")


@dataclass(frozen=True)
class RisUnavailableRule(HealthRule):
    id: str = "ris_unavailable"
    title: str = "RIS unavailable"
    description: str = "RIS should return device registration data."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.metadata.get("ris_unavailable"):
            return _fail(self, node, "RIS data unavailable.", "Verify RIS service and database connectivity.")
        return _pass(self, node, "RIS data available or not reported.")


@dataclass(frozen=True)
class RoutePatternMissingRule(HealthRule):
    id: str = "route_pattern_missing"
    title: str = "Route pattern missing"
    description: str = "Route plan should include pattern for destination."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.metadata.get("route_pattern_missing"):
            return _fail(self, node, "Route pattern missing.", "Create or enable required route pattern.")
        return _pass(self, node, "Route pattern state not reported as missing.")


@dataclass(frozen=True)
class CssMissingRule(HealthRule):
    id: str = "css_missing"
    title: str = "CSS missing"
    description: str = "Calling search space should include required partitions."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.metadata.get("css_missing"):
            return _fail(self, node, "CSS missing required partition.", "Update CSS membership.")
        return _pass(self, node, "CSS state not reported as missing.")


@dataclass(frozen=True)
class PartitionMissingRule(HealthRule):
    id: str = "partition_missing"
    title: str = "Partition missing"
    description: str = "Required partition must exist and be accessible."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_CUCM_NODE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        node = _require_type(obj, CUCMNode)
        if node.metadata.get("partition_missing"):
            return _fail(self, node, "Partition missing.", "Add partition to CSS.")
        return _pass(self, node, "Partition state not reported as missing.")


CUCM_HEALTH_RULES: tuple[HealthRule, ...] = (
    PhoneNotRegisteredRule(),
    DbReplicationUnhealthyRule(),
    CallManagerServiceStoppedRule(),
    TftpServiceStoppedRule(),
    CertificateExpiredRule(),
    SipTrunkDownRule(),
    RisUnavailableRule(),
    RoutePatternMissingRule(),
    CssMissingRule(),
    PartitionMissingRule(),
)


def register_cucm_health_rules(registry) -> None:
    for rule in CUCM_HEALTH_RULES:
        registry.register(rule)


def _require_type(obj: VoiceObject, expected_type):
    if not isinstance(obj, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(obj).__name__}")
    return obj


def _fail(rule: HealthRule, obj: VoiceObject, message: str, recommendation: str) -> HealthResult:
    return HealthResult(
        rule_id=rule.id,
        title=rule.title,
        description=rule.description,
        category=rule.category,
        severity=rule.severity,
        status=HealthStatus.FAIL,
        object_id=obj.id,
        object_type=obj.object_type,
        message=message,
        recommendation=recommendation,
    )


def _pass(rule: HealthRule, obj: VoiceObject, message: str) -> HealthResult:
    return HealthResult(
        rule_id=rule.id,
        title=rule.title,
        description=rule.description,
        category=rule.category,
        severity=rule.severity,
        status=HealthStatus.PASS,
        object_id=obj.id,
        object_type=obj.object_type,
        message=message,
        recommendation=None,
    )
