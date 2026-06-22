"""Microsoft Teams investigation constants and deterministic engine rules."""

from __future__ import annotations

from runtime.correlation_engine import CorrelationRule, CORRELATION_TYPE_REINFORCEMENT
from runtime.hypothesis_engine import HypothesisRule
from runtime.recommendation_engine import HypothesisActionPlan

VP_TEAMS_0001_PLAYBOOK_ID = "VP-TEAMS-0001"

TEAMS_INTAKE_ANSWERS = [
    "yes",
    "2026-06-19",
    "teams phone outbound calling failure",
    "contoso tenant users",
    "direct routing",
    "no",
]

TEAMS_EVIDENCE_FILES: tuple[tuple[str, str], ...] = (
    ("get-csonlineuser", "get_csonlineuser.txt"),
    ("get-csonlinevoiceroutingpolicy", "get_csonlinevoiceroutingpolicy.txt"),
    ("get-csonlinevoiceroute", "get_csonlinevoiceroute.txt"),
    ("get-csonlinepstngateway", "get_csonlinepstngateway.txt"),
    ("get-csphonenumberassignment", "get_csphonenumberassignment.csv"),
    ("get-csonlinelislocation", "get_csonlinelislocation.txt"),
    ("get-csresourceaccount", "get_csresourceaccount.txt"),
)

TEAMS_ALL_FAIL_EVIDENCE = [command for command, _ in TEAMS_EVIDENCE_FILES]

# Hypothesis titles
HYP_TEAMS_PHONE_LICENSE = "Teams Phone license missing"
HYP_ENTERPRISE_VOICE = "Enterprise Voice disabled"
HYP_PHONE_NUMBER = "Phone number not assigned"
HYP_VOICE_ROUTING_POLICY = "Voice Routing Policy missing"
HYP_PSTN_USAGE = "PSTN Usage missing"
HYP_VOICE_ROUTE = "Voice Route missing"
HYP_SBC_UNREACHABLE = "Direct Routing SBC unreachable"
HYP_TLS_CERTIFICATE = "TLS certificate expired"
HYP_SIP_OPTIONS = "SIP OPTIONS failed"
HYP_EMERGENCY_CALLING = "Emergency Calling configuration issue"
HYP_RESOURCE_ACCOUNT = "Resource Account issue"

VP_TEAMS_0001_RULES: tuple[HypothesisRule, ...] = (
    HypothesisRule(
        rule_id="HYP-TEAMS-LICENSE",
        title=HYP_TEAMS_PHONE_LICENSE,
        confidence=90.0,
        required_signals=frozenset({"teams_phone_license_missing"}),
        supporting_signals=frozenset({"teams_phone_license_missing", "enterprise_voice_disabled"}),
        explanation="Teams Phone license is not assigned to the affected user.",
        next_best_action="Review Microsoft 365 license assignment for Phone System.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-EV-VOICE",
        title=HYP_ENTERPRISE_VOICE,
        confidence=88.0,
        required_signals=frozenset({"enterprise_voice_disabled"}),
        supporting_signals=frozenset({"enterprise_voice_disabled", "phone_number_assignment_failed"}),
        explanation="Enterprise Voice is disabled on the Teams user.",
        next_best_action="Enable Enterprise Voice and assign telephone number.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-NUMBER",
        title=HYP_PHONE_NUMBER,
        confidence=86.0,
        required_signals=frozenset({"phone_number_assignment_failed"}),
        supporting_signals=frozenset({"phone_number_assignment_failed", "enterprise_voice_disabled"}),
        explanation="No telephone number is assigned to the Teams user.",
        next_best_action="Assign LineUri or phone number via Teams admin or PowerShell export review.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-VRP",
        title=HYP_VOICE_ROUTING_POLICY,
        confidence=87.0,
        required_signals=frozenset({"voice_routing_policy_missing"}),
        supporting_signals=frozenset({"voice_routing_policy_missing", "voice_routing_failure_pstn"}),
        explanation="Voice routing policy is missing or incomplete.",
        next_best_action="Assign voice routing policy with valid PSTN usages.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-PSTN-USAGE",
        title=HYP_PSTN_USAGE,
        confidence=85.0,
        required_signals=frozenset({"pstn_usage_missing"}),
        supporting_signals=frozenset({"pstn_usage_missing", "voice_routing_policy_missing"}),
        explanation="Voice routing policy has no PSTN usage assignments.",
        next_best_action="Add PSTN usage records and associate with voice routing policy.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-VOICE-ROUTE",
        title=HYP_VOICE_ROUTE,
        confidence=84.0,
        required_signals=frozenset({"voice_route_missing"}),
        supporting_signals=frozenset({"voice_route_missing", "voice_routing_failure_pstn"}),
        explanation="Required voice route is missing or incomplete.",
        next_best_action="Create or repair online voice route and PSTN gateway references.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-SBC",
        title=HYP_SBC_UNREACHABLE,
        confidence=92.0,
        required_signals=frozenset({"direct_routing_sbc_unreachable"}),
        supporting_signals=frozenset({"direct_routing_sbc_unreachable", "sbc_connectivity_lost"}),
        explanation="Direct Routing PSTN gateway is disabled or unreachable.",
        next_best_action="Restore SBC connectivity and validate trunk registration.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-TLS",
        title=HYP_TLS_CERTIFICATE,
        confidence=91.0,
        required_signals=frozenset({"tls_certificate_expired"}),
        supporting_signals=frozenset({"tls_certificate_expired", "direct_routing_sbc_unreachable"}),
        explanation="TLS certificate on the PSTN gateway or SBC is expired.",
        next_best_action="Renew TLS certificate and validate certificate chain.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-SIP-OPTIONS",
        title=HYP_SIP_OPTIONS,
        confidence=89.0,
        required_signals=frozenset({"sip_options_failure"}),
        supporting_signals=frozenset({"sip_options_failure", "direct_routing_sbc_unreachable"}),
        explanation="SIP OPTIONS health check to the SBC is failing.",
        next_best_action="Verify SBC responds to SIP OPTIONS and firewall permits keepalive.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-E911",
        title=HYP_EMERGENCY_CALLING,
        confidence=93.0,
        required_signals=frozenset({"emergency_calling_policy_missing"}),
        supporting_signals=frozenset({"emergency_calling_policy_missing", "emergency_routing_policy_missing"}),
        explanation="Emergency calling configuration or LIS location data is incomplete.",
        next_best_action="Assign emergency calling policies and validate LIS civic address.",
    ),
    HypothesisRule(
        rule_id="HYP-TEAMS-RESOURCE",
        title=HYP_RESOURCE_ACCOUNT,
        confidence=87.0,
        required_signals=frozenset({"resource_account_missing_license"}),
        supporting_signals=frozenset({"resource_account_missing_license", "auto_attendant_transfer_failure"}),
        explanation="Resource account is missing license or telephone number.",
        next_best_action="Assign Phone System license and phone number to resource account.",
    ),
)

VP_TEAMS_0001_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    CorrelationRule(
        rule_id="license_enterprise_voice",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"teams_phone_license_missing", "enterprise_voice_disabled"}),
        hypothesis_title=HYP_TEAMS_PHONE_LICENSE,
        confidence_delta=8.0,
        explanation="Missing Teams Phone license with Enterprise Voice disabled reinforces licensing root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="routing_policy_pstn_usage",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"voice_routing_policy_missing", "pstn_usage_missing"}),
        hypothesis_title=HYP_PSTN_USAGE,
        confidence_delta=7.0,
        explanation="Voice routing policy gap with missing PSTN usage reinforces routing policy failure.",
    ),
    CorrelationRule(
        rule_id="voice_route_gateway",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"voice_route_missing", "voice_routing_failure_pstn"}),
        hypothesis_title=HYP_VOICE_ROUTE,
        confidence_delta=8.0,
        explanation="Missing voice route with PSTN gateway gap reinforces route configuration failure.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="sbc_tls_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"direct_routing_sbc_unreachable", "tls_certificate_expired"}),
        hypothesis_title=HYP_TLS_CERTIFICATE,
        confidence_delta=9.0,
        explanation="Unreachable SBC with expired TLS certificate reinforces certificate root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="sbc_sip_options",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"direct_routing_sbc_unreachable", "sip_options_failure"}),
        hypothesis_title=HYP_SIP_OPTIONS,
        confidence_delta=8.0,
        explanation="Unreachable SBC with SIP OPTIONS failure reinforces keepalive root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="emergency_lis_location",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"emergency_calling_policy_missing", "emergency_routing_policy_missing"}),
        hypothesis_title=HYP_EMERGENCY_CALLING,
        confidence_delta=7.0,
        explanation="Missing emergency calling and routing policies reinforce E911 configuration issue.",
        apply_max_cap=True,
    ),
)

VP_TEAMS_0001_ACTION_PLANS: dict[str, HypothesisActionPlan] = {
    "HYP-TEAMS-LICENSE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-006 licensing validation runbook",
            "Assign Teams Phone or Phone System license in Microsoft 365 admin center",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-001 Teams client verification guide",),
        rollback_guidance=("Remove incorrect license assignment if applied to wrong user",),
        command="get-csonlineuser",
    ),
    "HYP-TEAMS-EV-VOICE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-006 licensing validation runbook",
            "Enable Enterprise Voice and assign telephone number",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-001 Teams client verification guide",),
        command="get-csonlineuser",
    ),
    "HYP-TEAMS-NUMBER": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-001 voice routing validation runbook",
            "Assign telephone number via Teams admin or number assignment export",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-002 voice routing verification guide",),
        command="get-csphonenumberassignment",
    ),
    "HYP-TEAMS-VRP": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-002 voice routing validation runbook",
            "Assign voice routing policy with valid PSTN usages",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-002 voice routing verification guide",),
        command="get-csonlinevoiceroutingpolicy",
    ),
    "HYP-TEAMS-PSTN-USAGE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-002 voice routing validation runbook",
            "Add PSTN usage and associate with voice routing policy",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-002 voice routing verification guide",),
        command="get-csonlinepstnusage",
    ),
    "HYP-TEAMS-VOICE-ROUTE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-002 voice routing validation runbook",
            "Create or repair online voice route and gateway references",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-002 voice routing verification guide",),
        command="get-csonlinevoiceroute",
    ),
    "HYP-TEAMS-SBC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-003 Direct Routing validation runbook",
            "Restore SBC connectivity and validate trunk registration",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-003 Direct Routing verification guide",),
        command="get-csonlinepstngateway",
        requires_engineer_approval=True,
    ),
    "HYP-TEAMS-TLS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-005 SBC certificate validation runbook",
            "Renew TLS certificate on SBC or reverse proxy",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-004 TLS verification guide",),
        command="get-csonlinepstngateway",
        requires_engineer_approval=True,
    ),
    "HYP-TEAMS-SIP-OPTIONS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-005 SBC certificate validation runbook",
            "Enable SIP OPTIONS response on SBC and verify firewall rules",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-003 Direct Routing verification guide",),
        command="get-csonlinepstngateway",
    ),
    "HYP-TEAMS-E911": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-007 emergency calling validation runbook",
            "Assign emergency calling policies and LIS locations",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-005 emergency calling verification guide",),
        command="get-csonlinelislocation",
        requires_engineer_approval=True,
    ),
    "HYP-TEAMS-RESOURCE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-MS-TEAMS-RB-009 resource account validation runbook",
            "Assign Phone System license and phone number to resource account",
        ),
        verification_steps=("Execute VP-MS-TEAMS-VG-009 resource account verification guide",),
        command="get-csresourceaccount",
    ),
}
