"""AudioCodes SBC health rules for AVOM."""

from __future__ import annotations

from dataclasses import dataclass

from health.health_categories import HealthCategory
from health.health_models import HealthResult, HealthStatus
from health.health_rule import HealthRule
from health.health_severity import HealthSeverity
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
from model.voice_graph import (
    OBJECT_TYPE_AUDIOCODES_CERTIFICATE,
    OBJECT_TYPE_AUDIOCODES_HA_CLUSTER,
    OBJECT_TYPE_AUDIOCODES_IP_GROUP,
    OBJECT_TYPE_AUDIOCODES_IP_PROFILE,
    OBJECT_TYPE_AUDIOCODES_LICENSE,
    OBJECT_TYPE_AUDIOCODES_MANIPULATION_SET,
    OBJECT_TYPE_AUDIOCODES_MEDIA_REALM,
    OBJECT_TYPE_AUDIOCODES_MEDIA_SECURITY_PROFILE,
    OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS,
    OBJECT_TYPE_AUDIOCODES_PROXY_SET,
    OBJECT_TYPE_AUDIOCODES_ROUTING_RULE,
    OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,
    OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,
    OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY,
    OBJECT_TYPE_AUDIOCODES_TLS_CONTEXT,
    VoiceObject,
)
from model.voice_topology import VoiceTopology


_DOWN_STATES = frozenset({"down", "disabled", "inactive", "unavailable", "failed", "offline"})
_UNAVAILABLE_STATES = frozenset({"unavailable", "down", "inactive", "offline"})


# ---------------------------------------------------------------------------
# SIP / Signaling
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SipOptionsFailedRule(HealthRule):
    id: str = "audiocodes_sip_options_failed"
    title: str = "SIP OPTIONS failed"
    description: str = "SBC SIP OPTIONS keepalive must succeed for trunk health."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        policy = _require_type(obj, SIPMessagePolicy)
        status = (_meta_text(policy, "options_status", "status") or "").lower()
        if policy.options_enabled is False or _meta_flag(policy, "sip_options_failure", "sip_options_failed"):
            return _fail(self, policy, "SIP OPTIONS keepalive failed.")
        if status in {"failed", "failure", "timeout", "down"}:
            return _fail(self, policy, "SIP OPTIONS keepalive failed.")
        return _pass(self, policy, "SIP OPTIONS state not reported as failed.")


@dataclass(frozen=True)
class Provider503Rule(HealthRule):
    id: str = "audiocodes_provider_503"
    title: str = "Provider 503 detected"
    description: str = "SIP 503 from provider indicates trunk overload or maintenance."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY,
        OBJECT_TYPE_AUDIOCODES_PROXY_SET,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, SIPMessagePolicy):
            status = (_meta_text(obj, "options_status", "sip_response", "status") or "").lower()
            if _meta_flag(obj, "provider_503") or status in {"503", "service unavailable"}:
                return _fail(self, obj, "Provider returned SIP 503.")
            return _pass(self, obj, "Provider 503 not detected on SIP message policy.")
        proxy_set = _require_type(obj, ProxySet)
        if _meta_flag(proxy_set, "provider_503") or _state_matches(proxy_set.state, {"503"}):
            return _fail(self, proxy_set, "Provider returned SIP 503.")
        return _pass(self, proxy_set, "Provider 503 not detected on Proxy Set.")


@dataclass(frozen=True)
class Timeout408Rule(HealthRule):
    id: str = "audiocodes_timeout_408"
    title: str = "408 timeout detected"
    description: str = "SIP 408 timeout indicates signaling path or peer response failure."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        sip_interface = _require_type(obj, SIPInterface)
        response = (_meta_text(sip_interface, "sip_response", "last_sip_response", "status") or "").lower()
        if _meta_flag(sip_interface, "timeout_408", "sip_timeout_408") or response in {"408", "timeout"}:
            return _fail(self, sip_interface, "SIP 408 timeout detected.")
        return _pass(self, sip_interface, "SIP 408 timeout not detected.")


@dataclass(frozen=True)
class Forbidden403Rule(HealthRule):
    id: str = "audiocodes_forbidden_403"
    title: str = "403 forbidden detected"
    description: str = "SIP 403 forbidden indicates authentication or policy rejection."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        sip_interface = _require_type(obj, SIPInterface)
        response = (_meta_text(sip_interface, "sip_response", "last_sip_response", "status") or "").lower()
        if _meta_flag(sip_interface, "forbidden_403", "sip_forbidden_403") or response in {"403", "forbidden"}:
            return _fail(self, sip_interface, "SIP 403 forbidden detected.")
        return _pass(self, sip_interface, "SIP 403 forbidden not detected.")


@dataclass(frozen=True)
class CodecMismatch488Rule(HealthRule):
    id: str = "audiocodes_codec_mismatch_488"
    title: str = "488 codec mismatch detected"
    description: str = "SIP 488 indicates incompatible codec negotiation."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,
        OBJECT_TYPE_AUDIOCODES_IP_PROFILE,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, SIPInterface):
            response = (_meta_text(obj, "sip_response", "last_sip_response", "status") or "").lower()
            if _meta_flag(obj, "codec_mismatch_488", "sip_codec_mismatch_488") or response in {"488", "not acceptable"}:
                return _fail(self, obj, "SIP 488 codec mismatch detected.")
            return _pass(self, obj, "SIP 488 codec mismatch not detected on SIP Interface.")
        profile = _require_type(obj, IPProfile)
        if _meta_flag(profile, "codec_mismatch_488"):
            return _fail(self, profile, "Codec mismatch detected on IP Profile.")
        return _pass(self, profile, "Codec mismatch not detected on IP Profile.")


# ---------------------------------------------------------------------------
# SBC Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProxySetUnavailableRule(HealthRule):
    id: str = "audiocodes_proxy_set_unavailable"
    title: str = "Proxy Set unavailable"
    description: str = "Proxy Sets must be available for provider connectivity."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_PROXY_SET,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        proxy_set = _require_type(obj, ProxySet)
        if _meta_flag(proxy_set, "proxy_set_unavailable") or _state_is_unavailable(proxy_set.state):
            return _fail(self, proxy_set, "Proxy Set is unavailable.")
        return _pass(self, proxy_set, "Proxy Set is available or state unknown.")


@dataclass(frozen=True)
class IpGroupDisabledRule(HealthRule):
    id: str = "audiocodes_ip_group_disabled"
    title: str = "IP Group disabled"
    description: str = "Disabled IP Groups cannot process calls."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_IP_GROUP,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        ip_group = _require_type(obj, IPGroup)
        if _meta_flag(ip_group, "ip_group_disabled") or _state_is_down(ip_group.state):
            return _fail(self, ip_group, "IP Group is disabled.")
        return _pass(self, ip_group, "IP Group is enabled or state unknown.")


@dataclass(frozen=True)
class SipInterfaceDownRule(HealthRule):
    id: str = "audiocodes_sip_interface_down"
    title: str = "SIP Interface down"
    description: str = "SIP Interfaces must be active for signaling."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        sip_interface = _require_type(obj, SIPInterface)
        if _meta_flag(sip_interface, "sip_interface_down") or _state_is_down(sip_interface.state):
            return _fail(self, sip_interface, "SIP Interface is down.")
        return _pass(self, sip_interface, "SIP Interface is active or state unknown.")


@dataclass(frozen=True)
class RoutingRuleMissingRule(HealthRule):
    id: str = "audiocodes_routing_rule_missing"
    title: str = "Routing Rule missing"
    description: str = "Routing rules require destination and IP Group assignment."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_ROUTING_RULE,
        OBJECT_TYPE_AUDIOCODES_IP_GROUP,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, RoutingRule):
            if not _has_text(obj.destination) or not _has_text(obj.ip_group):
                return _fail(self, obj, "Routing rule is missing destination or IP Group.")
            if _meta_flag(obj, "routing_table_issue", "routing_rule_missing"):
                return _fail(self, obj, "Routing rule configuration is incomplete.")
            return _pass(self, obj, "Routing rule has destination and IP Group.")
        ip_group = _require_type(obj, IPGroup)
        group_name = ip_group.ip_group_name or ip_group.name
        if not group_name:
            return _pass(self, ip_group, "IP Group identity unavailable for routing check.")
        if not topology.audiocodes_routing_rules:
            return _fail(self, ip_group, "No routing rules are configured.")
        referenced = any(
            rule.ip_group == group_name for rule in topology.audiocodes_routing_rules
        )
        if not referenced:
            return _fail(self, ip_group, "No routing rule references this IP Group.")
        if _meta_flag(ip_group, "routing_rule_missing"):
            return _fail(self, ip_group, "Required routing rule is missing.")
        return _pass(self, ip_group, "Routing rule reference is present or not evaluable.")


@dataclass(frozen=True)
class ManipulationSetMissingRule(HealthRule):
    id: str = "audiocodes_manipulation_set_missing"
    title: str = "Manipulation Set missing"
    description: str = "Manipulation Sets must be configured and active."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_MANIPULATION_SET,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        manipulation_set = _require_type(obj, ManipulationSet)
        if _meta_flag(manipulation_set, "manipulation_set_failure", "manipulation_set_missing"):
            return _fail(self, manipulation_set, "Manipulation Set is missing or failed.")
        if not _has_text(manipulation_set.set_name):
            return _fail(self, manipulation_set, "Manipulation Set name is missing.")
        if _state_is_down(manipulation_set.state):
            return _fail(self, manipulation_set, "Manipulation Set is inactive.")
        return _pass(self, manipulation_set, "Manipulation Set is configured.")


# ---------------------------------------------------------------------------
# TLS / Security
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TlsCertificateExpiredRule(HealthRule):
    id: str = "audiocodes_tls_certificate_expired"
    title: str = "TLS certificate expired"
    description: str = "Expired TLS certificates break secure SIP trunks."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_CERTIFICATE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        certificate = _require_type(obj, Certificate)
        status = (certificate.status or "").lower()
        if _meta_flag(certificate, "tls_certificate_expired") or status in {"expired", "invalid"}:
            return _fail(self, certificate, "TLS certificate is expired.")
        return _pass(self, certificate, "TLS certificate is valid or state unknown.")


@dataclass(frozen=True)
class TlsContextMissingRule(HealthRule):
    id: str = "audiocodes_tls_context_missing"
    title: str = "TLS context missing"
    description: str = "TLS SIP Interfaces require an assigned TLS context."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        sip_interface = _require_type(obj, SIPInterface)
        transport = (sip_interface.transport or "").lower()
        if transport == "tls" and not _has_text(sip_interface.tls_context):
            return _fail(self, sip_interface, "TLS context is missing on TLS SIP Interface.")
        if _meta_flag(sip_interface, "tls_context_missing"):
            return _fail(self, sip_interface, "TLS context is missing.")
        return _pass(self, sip_interface, "TLS context is assigned or transport is not TLS.")


@dataclass(frozen=True)
class TlsNegotiationFailureRule(HealthRule):
    id: str = "audiocodes_tls_negotiation_failure"
    title: str = "TLS negotiation failure"
    description: str = "TLS handshake failures prevent secure signaling."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_TLS_CONTEXT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        tls_context = _require_type(obj, TLSContext)
        status = (_meta_text(tls_context, "status", "state") or "").lower()
        if _meta_flag(tls_context, "tls_negotiation_failure") or status in {
            "failed",
            "error",
            "negotiation_failed",
        }:
            return _fail(self, tls_context, "TLS negotiation failed.")
        return _pass(self, tls_context, "TLS negotiation state not reported as failed.")


@dataclass(frozen=True)
class SipFloodProtectionRule(HealthRule):
    id: str = "audiocodes_sip_flood_protection"
    title: str = "SIP flood protection triggered"
    description: str = "SIP flood protection indicates abnormal signaling volume."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        device = _require_type(obj, SBCDevice)
        if _meta_flag(device, "sip_flood_protection", "sip_flood_protection_triggered"):
            return _fail(self, device, "SIP flood protection is active.")
        return _pass(self, device, "SIP flood protection not reported as triggered.")


@dataclass(frozen=True)
class DosProtectionRule(HealthRule):
    id: str = "audiocodes_dos_protection"
    title: str = "DoS protection activated"
    description: str = "DoS protection indicates attack or overload mitigation."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        device = _require_type(obj, SBCDevice)
        if _meta_flag(device, "dos_protection", "dos_protection_activated"):
            return _fail(self, device, "DoS protection is active.")
        return _pass(self, device, "DoS protection not reported as activated.")


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MediaRealmMissingRule(HealthRule):
    id: str = "audiocodes_media_realm_missing"
    title: str = "Media Realm missing"
    description: str = "IP Groups and SIP Interfaces require a Media Realm assignment."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_IP_GROUP,
        OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, IPGroup):
            if not _has_text(obj.media_realm) or _meta_flag(obj, "media_realm_missing"):
                return _fail(self, obj, "Media Realm is not assigned to IP Group.")
            return _pass(self, obj, "Media Realm is assigned to IP Group.")
        sip_interface = _require_type(obj, SIPInterface)
        if not _has_text(sip_interface.media_realm) or _meta_flag(sip_interface, "media_realm_missing"):
            return _fail(self, sip_interface, "Media Realm is not assigned to SIP Interface.")
        return _pass(self, sip_interface, "Media Realm is assigned to SIP Interface.")


@dataclass(frozen=True)
class MediaRealmDownRule(HealthRule):
    id: str = "audiocodes_media_realm_down"
    title: str = "Media Realm down"
    description: str = "Media Realms must be active for RTP processing."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_MEDIA_REALM,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        media_realm = _require_type(obj, MediaRealm)
        if _meta_flag(media_realm, "media_realm_failure", "media_realm_down") or _state_is_down(
            media_realm.state
        ):
            return _fail(self, media_realm, "Media Realm is down.")
        return _pass(self, media_realm, "Media Realm is active or state unknown.")


@dataclass(frozen=True)
class RtpOneWayAudioRule(HealthRule):
    id: str = "audiocodes_rtp_one_way_audio"
    title: str = "RTP one-way audio detected"
    description: str = "One-way RTP indicates media path or firewall issues."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_MEDIA_REALM,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        media_realm = _require_type(obj, MediaRealm)
        if _meta_flag(media_realm, "rtp_one_way_audio"):
            return _fail(self, media_realm, "RTP one-way audio detected.")
        if not _has_text(media_realm.ip_address):
            return _fail(self, media_realm, "Media Realm media IP is missing.")
        return _pass(self, media_realm, "RTP path not reported as one-way.")


@dataclass(frozen=True)
class SrtpMismatchRule(HealthRule):
    id: str = "audiocodes_srtp_mismatch"
    title: str = "SRTP mismatch detected"
    description: str = "SRTP mode mismatch prevents secure media."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_MEDIA_SECURITY_PROFILE,
        OBJECT_TYPE_AUDIOCODES_IP_PROFILE,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, MediaSecurityProfile):
            mode = (obj.srtp_mode or "").lower()
            if _meta_flag(obj, "srtp_mismatch") or mode in {"disabled", "mismatch", "failed"}:
                return _fail(self, obj, "SRTP mode mismatch detected.")
            return _pass(self, obj, "SRTP mode is consistent on media security profile.")
        profile = _require_type(obj, IPProfile)
        if _meta_flag(profile, "srtp_mismatch"):
            return _fail(self, profile, "SRTP mismatch detected on IP Profile.")
        expected = _meta_bool(profile, "peer_srtp_enabled")
        if expected is not None and profile.enable_srtp is not None and profile.enable_srtp != expected:
            return _fail(self, profile, "SRTP settings mismatch with peer.")
        return _pass(self, profile, "SRTP settings are consistent.")


# ---------------------------------------------------------------------------
# HA / Licensing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HaStandbyNotSynchronizedRule(HealthRule):
    id: str = "audiocodes_standby_synchronization_failure"
    title: str = "HA standby not synchronized"
    description: str = "HA standby nodes must remain synchronized."
    category: HealthCategory = HealthCategory.HIGH_AVAILABILITY
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_HA_CLUSTER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        cluster = _require_type(obj, HACluster)
        sync_state = (cluster.sync_state or "").lower()
        if _meta_flag(cluster, "standby_synchronization_failure") or sync_state in {
            "out_of_sync",
            "failed",
            "desynchronized",
            "not_synchronized",
        }:
            return _fail(self, cluster, "HA standby is not synchronized.")
        return _pass(self, cluster, "HA standby synchronization is healthy or unknown.")


@dataclass(frozen=True)
class HaFailoverActiveRule(HealthRule):
    id: str = "audiocodes_ha_failover"
    title: str = "HA failover active"
    description: str = "Active HA failover indicates cluster instability."
    category: HealthCategory = HealthCategory.HIGH_AVAILABILITY
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_HA_CLUSTER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        cluster = _require_type(obj, HACluster)
        cluster_state = (cluster.cluster_state or "").lower()
        if _meta_flag(cluster, "ha_failover") or cluster_state in {"failover", "failed_over"}:
            return _fail(self, cluster, "HA failover is active.")
        return _pass(self, cluster, "HA failover is not active.")


@dataclass(frozen=True)
class SessionLicenseExhaustedRule(HealthRule):
    id: str = "audiocodes_session_license_exhausted"
    title: str = "Session license exhausted"
    description: str = "Session license exhaustion blocks new calls."
    category: HealthCategory = HealthCategory.PERFORMANCE
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_LICENSE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        license_obj = _require_type(obj, License)
        if _meta_flag(license_obj, "session_license_exhausted"):
            return _fail(self, license_obj, "Session license is exhausted.")
        total = license_obj.sessions_total
        used = license_obj.sessions_used
        if total is not None and used is not None and used >= total:
            return _fail(self, license_obj, "Session license is exhausted.")
        return _pass(self, license_obj, "Session license capacity is available.")


@dataclass(frozen=True)
class SbcLicenseInvalidRule(HealthRule):
    id: str = "audiocodes_sbc_license_invalid"
    title: str = "SBC license invalid"
    description: str = "Invalid SBC licenses restrict platform features."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_AUDIOCODES_LICENSE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        license_obj = _require_type(obj, License)
        status = (_meta_text(license_obj, "license_status", "status") or "").lower()
        if _meta_flag(license_obj, "sbc_license_invalid", "license_invalid"):
            return _fail(self, license_obj, "SBC license is invalid.")
        if status in {"invalid", "expired", "revoked"}:
            return _fail(self, license_obj, "SBC license is invalid.")
        return _pass(self, license_obj, "SBC license is valid or state unknown.")


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GatewayUnreachableRule(HealthRule):
    id: str = "audiocodes_gateway_unreachable"
    title: str = "Gateway unreachable"
    description: str = "Provider gateways must be reachable for outbound calls."
    category: HealthCategory = HealthCategory.NETWORK
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS,
        OBJECT_TYPE_AUDIOCODES_PROXY_SET,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, ProxyAddress):
            if _meta_flag(obj, "gateway_unreachable", "pstn_gateway_unreachable"):
                return _fail(self, obj, "Gateway is unreachable.")
            if not _has_text(obj.address):
                return _fail(self, obj, "Proxy address is missing.")
            return _pass(self, obj, "Gateway address is present and reachable.")
        proxy_set = _require_type(obj, ProxySet)
        if _meta_flag(proxy_set, "gateway_unreachable"):
            return _fail(self, proxy_set, "Gateway is unreachable.")
        return _pass(self, proxy_set, "Gateway reachability not reported as failed.")


@dataclass(frozen=True)
class DnsResolutionFailureRule(HealthRule):
    id: str = "audiocodes_dns_resolution_failure"
    title: str = "DNS resolution failure"
    description: str = "DNS failures prevent FQDN-based trunk resolution."
    category: HealthCategory = HealthCategory.NETWORK
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,
        OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, SBCDevice):
            if _meta_flag(obj, "dns_resolution_failure"):
                return _fail(self, obj, "DNS resolution failed on SBC.")
            return _pass(self, obj, "DNS resolution not reported as failed on SBC.")
        address = _require_type(obj, ProxyAddress)
        if _meta_flag(address, "dns_resolution_failure"):
            return _fail(self, address, "DNS resolution failed for gateway address.")
        host = _meta_text(address, "fqdn", "hostname")
        if host and not _has_text(address.address):
            return _fail(self, address, "DNS resolution failed for gateway FQDN.")
        return _pass(self, address, "DNS resolution not reported as failed.")


AUDIOCODES_HEALTH_RULES: tuple[HealthRule, ...] = (
    SipOptionsFailedRule(),
    Provider503Rule(),
    Timeout408Rule(),
    Forbidden403Rule(),
    CodecMismatch488Rule(),
    ProxySetUnavailableRule(),
    IpGroupDisabledRule(),
    SipInterfaceDownRule(),
    RoutingRuleMissingRule(),
    ManipulationSetMissingRule(),
    TlsCertificateExpiredRule(),
    TlsContextMissingRule(),
    TlsNegotiationFailureRule(),
    SipFloodProtectionRule(),
    DosProtectionRule(),
    MediaRealmMissingRule(),
    MediaRealmDownRule(),
    RtpOneWayAudioRule(),
    SrtpMismatchRule(),
    HaStandbyNotSynchronizedRule(),
    HaFailoverActiveRule(),
    SessionLicenseExhaustedRule(),
    SbcLicenseInvalidRule(),
    GatewayUnreachableRule(),
    DnsResolutionFailureRule(),
)


def register_audiocodes_health_rules(registry) -> None:
    """Register AudioCodes SBC health rules."""
    for rule in AUDIOCODES_HEALTH_RULES:
        registry.register(rule)


def _require_type(obj: VoiceObject, expected_type: type):
    if not isinstance(obj, expected_type):
        raise TypeError(f"Expected {expected_type.__name__}, got {type(obj).__name__}")
    return obj


def _metadata(obj: VoiceObject) -> dict:
    return dict(obj.metadata or {})


def _meta_flag(obj: VoiceObject, *keys: str) -> bool:
    metadata = _metadata(obj)
    return any(metadata.get(key) is True for key in keys)


def _meta_bool(obj: VoiceObject, key: str) -> bool | None:
    value = _metadata(obj).get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "enabled"}:
            return True
        if normalized in {"false", "no", "0", "disabled"}:
            return False
    return None


def _meta_text(obj: VoiceObject, *keys: str) -> str | None:
    metadata = _metadata(obj)
    for key in keys:
        value = metadata.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def _state_is_down(state: str | None) -> bool:
    return _state_matches(state, _DOWN_STATES)


def _state_is_unavailable(state: str | None) -> bool:
    return _state_matches(state, _UNAVAILABLE_STATES)


def _state_matches(state: str | None, values: frozenset[str]) -> bool:
    if not state:
        return False
    return state.strip().lower() in values


def _fail(rule: HealthRule, obj: VoiceObject, message: str) -> HealthResult:
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
        recommendation=None,
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
