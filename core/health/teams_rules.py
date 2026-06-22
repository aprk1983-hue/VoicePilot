"""Microsoft Teams Phone health rules for CVOM."""

from __future__ import annotations

from dataclasses import dataclass

from health.health_categories import HealthCategory
from health.health_models import HealthResult, HealthStatus
from health.health_rule import HealthRule
from health.health_severity import HealthSeverity
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
from model.voice_graph import (
    OBJECT_TYPE_TEAMS_AUTO_ATTENDANT,
    OBJECT_TYPE_TEAMS_CALL_QUEUE,
    OBJECT_TYPE_TEAMS_LIS_LOCATION,
    OBJECT_TYPE_TEAMS_PHONE_NUMBER,
    OBJECT_TYPE_TEAMS_PSTN_GATEWAY,
    OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT,
    OBJECT_TYPE_TEAMS_USER,
    OBJECT_TYPE_TEAMS_VOICE_ROUTE,
    OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY,
    VoiceObject,
)
from model.voice_topology import VoiceTopology


# ---------------------------------------------------------------------------
# Licensing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TeamsPhoneLicenseMissingRule(HealthRule):
    id: str = "teams_phone_license_missing"
    title: str = "Teams Phone license missing"
    description: str = "Teams Phone users require a Phone System license."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if _meta_flag(user, "teams_phone_license_missing") or _meta_bool(user, "teams_phone_license_assigned") is False:
            return _fail(self, user, "Teams Phone license is not assigned.")
        return _pass(self, user, "Teams Phone license state not reported as missing.")


@dataclass(frozen=True)
class EnterpriseVoiceDisabledRule(HealthRule):
    id: str = "enterprise_voice_disabled"
    title: str = "Enterprise Voice disabled"
    description: str = "Enterprise Voice must be enabled for PSTN calling."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if user.enterprise_voice_enabled is False:
            return _fail(self, user, "Enterprise Voice is disabled.")
        return _pass(self, user, "Enterprise Voice is enabled or state unknown.")


@dataclass(frozen=True)
class CallingPlanLicenseMissingRule(HealthRule):
    id: str = "calling_plan_license_missing"
    title: str = "Calling Plan license missing"
    description: str = "Calling Plan users require a Microsoft Calling Plan license."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if _meta_flag(user, "calling_plan_license_missing") or _meta_bool(user, "calling_plan_license_assigned") is False:
            return _fail(self, user, "Calling Plan license is not assigned.")
        return _pass(self, user, "Calling Plan license state not reported as missing.")


@dataclass(frozen=True)
class ResourceAccountLicenseMissingRule(HealthRule):
    id: str = "resource_account_license_missing"
    title: str = "Resource Account license missing"
    description: str = "Resource accounts require a Phone System license."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        account = _require_type(obj, TeamsResourceAccount)
        if _meta_flag(account, "resource_account_license_missing") or _meta_bool(account, "license_assigned") is False:
            return _fail(self, account, "Resource account license is not assigned.")
        return _pass(self, account, "Resource account license state not reported as missing.")


# ---------------------------------------------------------------------------
# User configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhoneNumberNotAssignedRule(HealthRule):
    id: str = "phone_number_not_assigned"
    title: str = "Phone number not assigned"
    description: str = "Teams Phone users require an assigned telephone number."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if not _has_text(user.line_uri) or _meta_flag(user, "phone_number_not_assigned"):
            return _fail(self, user, "No telephone number is assigned to the user.")
        return _pass(self, user, "Telephone number is assigned or not required.")


@dataclass(frozen=True)
class VoiceRoutingPolicyMissingRule(HealthRule):
    id: str = "voice_routing_policy_missing"
    title: str = "Voice Routing Policy missing"
    description: str = "Teams Phone users require a voice routing policy."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if not _has_text(user.voice_routing_policy) or _meta_flag(user, "voice_routing_policy_missing"):
            return _fail(self, user, "No voice routing policy is assigned.")
        return _pass(self, user, "Voice routing policy is assigned.")


@dataclass(frozen=True)
class TenantDialPlanMissingRule(HealthRule):
    id: str = "tenant_dial_plan_missing"
    title: str = "Tenant Dial Plan missing"
    description: str = "Teams Phone users should have a tenant dial plan."
    category: HealthCategory = HealthCategory.DIAL_PLAN
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        if not _has_text(user.dial_plan) or _meta_flag(user, "tenant_dial_plan_missing"):
            return _fail(self, user, "No tenant dial plan is assigned.")
        return _pass(self, user, "Tenant dial plan is assigned.")


@dataclass(frozen=True)
class CallerIdPolicyMissingRule(HealthRule):
    id: str = "caller_id_policy_missing"
    title: str = "Caller ID policy missing"
    description: str = "Teams Phone users should have a caller ID policy."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        caller_id = _meta_text(user, "caller_id_policy", "calling_line_identity", "online_caller_id_policy")
        if not caller_id or _meta_flag(user, "caller_id_policy_missing"):
            return _fail(self, user, "No caller ID policy is assigned.")
        return _pass(self, user, "Caller ID policy is assigned.")


@dataclass(frozen=True)
class LocationPolicyMissingRule(HealthRule):
    id: str = "location_policy_missing"
    title: str = "Location policy missing"
    description: str = "Teams Phone users should have a location policy for emergency services."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        location_policy = _meta_text(user, "location_policy", "enhanced_location_policy", "online_location_policy")
        if not location_policy or _meta_flag(user, "location_policy_missing"):
            return _fail(self, user, "No location policy is assigned.")
        return _pass(self, user, "Location policy is assigned.")


# ---------------------------------------------------------------------------
# Voice routing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PstnUsageMissingRule(HealthRule):
    id: str = "pstn_usage_missing"
    title: str = "PSTN Usage missing"
    description: str = "Voice routing policies require at least one PSTN usage."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        policy = _require_type(obj, TeamsVoiceRoutingPolicy)
        if not policy.pstn_usages or _meta_flag(policy, "pstn_usage_missing"):
            return _fail(self, policy, "Voice routing policy has no PSTN usages.")
        return _pass(self, policy, "Voice routing policy includes PSTN usages.")


@dataclass(frozen=True)
class VoiceRouteMissingRule(HealthRule):
    id: str = "voice_route_missing"
    title: str = "Voice Route missing"
    description: str = "Voice routing policies should reference reachable voice routes."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        policy = _require_type(obj, TeamsVoiceRoutingPolicy)
        if not policy.pstn_usages:
            return _pass(self, policy, "PSTN usage coverage not evaluated without usages.")
        if not topology.teams_voice_routes:
            return _fail(self, policy, "No voice routes are present in topology.")
        if not any(
            usage in route.online_pstn_usages
            for route in topology.teams_voice_routes
            for usage in policy.pstn_usages
        ):
            return _fail(self, policy, "No voice route references this policy PSTN usage.")
        return _pass(self, policy, "Voice route coverage exists for policy PSTN usages.")


@dataclass(frozen=True)
class VoiceRouteWithoutGatewayRule(HealthRule):
    id: str = "voice_route_without_gateway"
    title: str = "Voice Route without gateway"
    description: str = "Direct Routing voice routes require a PSTN gateway."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_VOICE_ROUTE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        route = _require_type(obj, TeamsVoiceRoute)
        if not route.online_pstn_gateway_list or _meta_flag(route, "voice_route_without_gateway"):
            return _fail(self, route, "Voice route has no PSTN gateway assignment.")
        return _pass(self, route, "Voice route references a PSTN gateway.")


@dataclass(frozen=True)
class GatewayNotReferencedRule(HealthRule):
    id: str = "gateway_not_referenced"
    title: str = "Gateway not referenced"
    description: str = "PSTN gateways should be referenced by at least one voice route."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.LOW
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        gateway_names = {name for name in (gateway.name, gateway.fqdn) if _has_text(name)}
        if not gateway_names:
            return _pass(self, gateway, "Gateway identity not available for reference check.")
        if not topology.teams_voice_routes:
            return _fail(self, gateway, "No voice routes reference this gateway.")
        referenced = any(
            gateway_name in route.online_pstn_gateway_list
            for route in topology.teams_voice_routes
            for gateway_name in gateway_names
        )
        if not referenced:
            return _fail(self, gateway, "Gateway is not referenced by any voice route.")
        return _pass(self, gateway, "Gateway is referenced by at least one voice route.")


# ---------------------------------------------------------------------------
# Direct Routing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SbcUnreachableRule(HealthRule):
    id: str = "sbc_unreachable"
    title: str = "SBC unreachable"
    description: str = "Direct Routing PSTN gateways must be reachable."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        if gateway.enabled is False or _meta_flag(gateway, "sbc_unreachable", "direct_routing_sbc_unreachable"):
            return _fail(self, gateway, "PSTN gateway is unreachable or disabled.")
        return _pass(self, gateway, "PSTN gateway is enabled and reachable.")


@dataclass(frozen=True)
class TlsCertificateExpiredRule(HealthRule):
    id: str = "tls_certificate_expired"
    title: str = "TLS certificate expired"
    description: str = "Direct Routing gateways require valid TLS certificates."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        if _meta_flag(gateway, "tls_certificate_expired"):
            return _fail(self, gateway, "TLS certificate is expired.")
        return _pass(self, gateway, "TLS certificate state not reported as expired.")


@dataclass(frozen=True)
class SipOptionsFailedRule(HealthRule):
    id: str = "sip_options_failed"
    title: str = "SIP OPTIONS failed"
    description: str = "Teams monitors SBC health using SIP OPTIONS."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        if _meta_flag(gateway, "sip_options_failed", "sip_options_failure"):
            return _fail(self, gateway, "SIP OPTIONS health check failed.")
        return _pass(self, gateway, "SIP OPTIONS state not reported as failed.")


@dataclass(frozen=True)
class MediaBypassDisabledRule(HealthRule):
    id: str = "media_bypass_disabled"
    title: str = "Media Bypass disabled"
    description: str = "Media bypass should be enabled where supported."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        if _meta_flag(gateway, "media_bypass_disabled") or _meta_bool(gateway, "media_bypass_enabled") is False:
            return _fail(self, gateway, "Media bypass is disabled.")
        return _pass(self, gateway, "Media bypass is enabled or state unknown.")


# ---------------------------------------------------------------------------
# Operator Connect
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OperatorConnectProviderMissingRule(HealthRule):
    id: str = "operator_connect_provider_missing"
    title: str = "Operator Connect provider missing"
    description: str = "Operator Connect numbers require a carrier provider assignment."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PHONE_NUMBER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        number = _require_type(obj, TeamsPhoneNumber)
        purpose = (number.assigned_purpose or "").lower()
        if "operator" in purpose and not _meta_text(number, "operator_connect_provider", "carrier_name", "operator_name"):
            return _fail(self, number, "Operator Connect provider is not assigned.")
        if _meta_flag(number, "operator_connect_provider_missing"):
            return _fail(self, number, "Operator Connect provider is not assigned.")
        return _pass(self, number, "Operator Connect provider is assigned or not applicable.")


@dataclass(frozen=True)
class OperatorConnectNumberUnassignedRule(HealthRule):
    id: str = "operator_connect_number_unassigned"
    title: str = "Operator Connect number unassigned"
    description: str = "Operator Connect telephone numbers must be assigned."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PHONE_NUMBER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        number = _require_type(obj, TeamsPhoneNumber)
        purpose = (number.assigned_purpose or "").lower()
        status = (number.assignment_status or "").lower()
        if "operator" in purpose and ("unassigned" in status or not _has_text(number.assigned_to)):
            return _fail(self, number, "Operator Connect number is unassigned.")
        if _meta_flag(number, "operator_connect_number_unassigned"):
            return _fail(self, number, "Operator Connect number is unassigned.")
        return _pass(self, number, "Operator Connect number is assigned or not applicable.")


# ---------------------------------------------------------------------------
# Emergency calling
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmergencyCallingPolicyMissingRule(HealthRule):
    id: str = "emergency_calling_policy_missing"
    title: str = "Emergency Calling Policy missing"
    description: str = "Teams Phone users require an emergency calling policy."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        policy = _meta_text(user, "emergency_calling_policy", "online_emergency_calling_policy")
        if not policy or _meta_flag(user, "emergency_calling_policy_missing"):
            return _fail(self, user, "No emergency calling policy is assigned.")
        return _pass(self, user, "Emergency calling policy is assigned.")


@dataclass(frozen=True)
class EmergencyRoutingPolicyMissingRule(HealthRule):
    id: str = "emergency_routing_policy_missing"
    title: str = "Emergency Routing Policy missing"
    description: str = "Teams Phone users require an emergency routing policy."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_USER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        user = _require_type(obj, TeamsUser)
        policy = _meta_text(user, "emergency_routing_policy", "online_emergency_routing_policy")
        if not policy or _meta_flag(user, "emergency_routing_policy_missing"):
            return _fail(self, user, "No emergency routing policy is assigned.")
        return _pass(self, user, "Emergency routing policy is assigned.")


@dataclass(frozen=True)
class LisLocationMissingRule(HealthRule):
    id: str = "lis_location_missing"
    title: str = "LIS Location missing"
    description: str = "Emergency locations require civic address or location data."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_LIS_LOCATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        location = _require_type(obj, TeamsLisLocation)
        if not _has_text(location.civic_address) and not _has_text(location.location):
            return _fail(self, location, "LIS location is missing civic address and location.")
        if location.e911_enabled is False:
            return _fail(self, location, "E911 is disabled for this LIS location.")
        return _pass(self, location, "LIS location includes emergency location data.")


@dataclass(frozen=True)
class TrustedIpMissingRule(HealthRule):
    id: str = "trusted_ip_missing"
    title: str = "Trusted IP missing"
    description: str = "Direct Routing deployments should declare trusted IP subnets."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_PSTN_GATEWAY,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        gateway = _require_type(obj, TeamsPstnGateway)
        trusted_ips = _meta_text(gateway, "trusted_ips", "trusted_ip_subnets")
        if _meta_flag(gateway, "trusted_ip_missing") or (trusted_ips is not None and not trusted_ips.strip()):
            return _fail(self, gateway, "Trusted IP subnets are not configured.")
        if trusted_ips is None and not _meta_flag(gateway, "trusted_ip_configured"):
            return _pass(self, gateway, "Trusted IP state not reported.")
        if trusted_ips:
            return _pass(self, gateway, "Trusted IP subnets are configured.")
        return _fail(self, gateway, "Trusted IP subnets are not configured.")


# ---------------------------------------------------------------------------
# Resource accounts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AutoAttendantMissingResourceAccountRule(HealthRule):
    id: str = "auto_attendant_missing_resource_account"
    title: str = "Auto Attendant missing Resource Account"
    description: str = "Auto attendants require an associated resource account."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_AUTO_ATTENDANT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        attendant = _require_type(obj, TeamsAutoAttendant)
        if _has_resource_account_reference(attendant, topology):
            return _pass(self, attendant, "Auto attendant references a resource account.")
        return _fail(self, attendant, "Auto attendant has no associated resource account.")


@dataclass(frozen=True)
class CallQueueMissingResourceAccountRule(HealthRule):
    id: str = "call_queue_missing_resource_account"
    title: str = "Call Queue missing Resource Account"
    description: str = "Call queues require an associated resource account."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_CALL_QUEUE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        queue = _require_type(obj, TeamsCallQueue)
        if _has_resource_account_reference(queue, topology):
            return _pass(self, queue, "Call queue references a resource account.")
        return _fail(self, queue, "Call queue has no associated resource account.")


@dataclass(frozen=True)
class ResourceAccountUnlicensedRule(HealthRule):
    id: str = "resource_account_unlicensed"
    title: str = "Resource Account unlicensed"
    description: str = "Resource accounts require licensing and a telephone number."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        account = _require_type(obj, TeamsResourceAccount)
        if not _has_text(account.phone_number) or _meta_flag(account, "resource_account_unlicensed"):
            return _fail(self, account, "Resource account is unlicensed or missing a phone number.")
        return _pass(self, account, "Resource account has a telephone number.")


TEAMS_HEALTH_RULES: tuple[HealthRule, ...] = (
    TeamsPhoneLicenseMissingRule(),
    EnterpriseVoiceDisabledRule(),
    CallingPlanLicenseMissingRule(),
    ResourceAccountLicenseMissingRule(),
    PhoneNumberNotAssignedRule(),
    VoiceRoutingPolicyMissingRule(),
    TenantDialPlanMissingRule(),
    CallerIdPolicyMissingRule(),
    LocationPolicyMissingRule(),
    PstnUsageMissingRule(),
    VoiceRouteMissingRule(),
    VoiceRouteWithoutGatewayRule(),
    GatewayNotReferencedRule(),
    SbcUnreachableRule(),
    TlsCertificateExpiredRule(),
    SipOptionsFailedRule(),
    MediaBypassDisabledRule(),
    OperatorConnectProviderMissingRule(),
    OperatorConnectNumberUnassignedRule(),
    EmergencyCallingPolicyMissingRule(),
    EmergencyRoutingPolicyMissingRule(),
    LisLocationMissingRule(),
    TrustedIpMissingRule(),
    AutoAttendantMissingResourceAccountRule(),
    CallQueueMissingResourceAccountRule(),
    ResourceAccountUnlicensedRule(),
)


def register_teams_health_rules(registry) -> None:
    """Register Microsoft Teams health rules."""
    for rule in TEAMS_HEALTH_RULES:
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
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
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


def _has_resource_account_reference(obj: VoiceObject, topology: VoiceTopology) -> bool:
    return bool(_meta_text(obj, "resource_account", "resource_account_id", "application_id"))


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
