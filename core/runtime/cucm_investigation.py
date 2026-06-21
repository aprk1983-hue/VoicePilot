"""Cisco CUCM investigation constants and deterministic engine rules."""

from __future__ import annotations

from runtime.correlation_engine import CorrelationRule, CORRELATION_TYPE_REINFORCEMENT
from runtime.hypothesis_engine import HypothesisRule
from runtime.recommendation_engine import HypothesisActionPlan

VP_CUCM_0001_PLAYBOOK_ID = "VP-CUCM-0001"

CUCM_INTAKE_ANSWERS = [
    "yes",
    "2026-06-19",
    "phone registration and call routing failure",
    "hq site users",
    "yes",
]

CUCM_EVIDENCE_FILES: tuple[tuple[str, str], ...] = (
    ("show risdb query phone", "show_risdb_query_phone.txt"),
    ("utils dbreplication runtimestate", "utils_dbreplication_runtimestate.txt"),
    ("utils service list", "utils_service_list.txt"),
    ("show sip trunk", "show_sip_trunk.txt"),
    ("show cert list", "show_cert_list.txt"),
)

CUCM_ALL_FAIL_EVIDENCE = [command for command, _ in CUCM_EVIDENCE_FILES]

# Hypothesis titles
HYP_PHONE_REGISTRATION = "Phone registration failure"
HYP_DB_REPLICATION = "Database replication issue"
HYP_CALLMANAGER_SERVICE = "CallManager service failure"
HYP_TFTP_SERVICE = "TFTP issue"
HYP_CERTIFICATE = "Certificate issue"
HYP_ROUTING = "Routing configuration issue"
HYP_CSS_MISMATCH = "CSS mismatch"
HYP_PARTITION_MISMATCH = "Partition mismatch"
HYP_MEDIA_RESOURCE = "Media resource issue"
HYP_SIP_TRUNK = "SIP trunk issue"

VP_CUCM_0001_RULES: tuple[HypothesisRule, ...] = (
    HypothesisRule(
        rule_id="HYP-CUCM-PHONE-REG",
        title=HYP_PHONE_REGISTRATION,
        confidence=88.0,
        required_signals=frozenset({"phone_not_registered"}),
        supporting_signals=frozenset({"phone_not_registered", "ris_unavailable"}),
        explanation="RIS shows one or more phones not registered to CUCM.",
        next_best_action="Review phone network reachability, device pool, and CM group assignment.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-DB-REP",
        title=HYP_DB_REPLICATION,
        confidence=92.0,
        required_signals=frozenset({"db_replication_unhealthy"}),
        supporting_signals=frozenset({"db_replication_unhealthy"}),
        explanation="Database replication is unhealthy between CUCM cluster nodes.",
        next_best_action="Run utils dbreplication status and resolve publisher-subscriber sync.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-CM-SVC",
        title=HYP_CALLMANAGER_SERVICE,
        confidence=94.0,
        required_signals=frozenset({"callmanager_service_stopped"}),
        supporting_signals=frozenset({"callmanager_service_stopped"}),
        explanation="Cisco CallManager service is not running on a cluster node.",
        next_best_action="Restart Cisco CallManager and review RTMT service alerts.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-TFTP",
        title=HYP_TFTP_SERVICE,
        confidence=90.0,
        required_signals=frozenset({"tftp_service_stopped"}),
        supporting_signals=frozenset({"tftp_service_stopped"}),
        explanation="Cisco TFTP service is stopped, blocking phone configuration download.",
        next_best_action="Start Cisco TFTP service and verify config file delivery.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-CERT",
        title=HYP_CERTIFICATE,
        confidence=91.0,
        required_signals=frozenset({"certificate_expired"}),
        supporting_signals=frozenset({"certificate_expired", "tls_handshake_failed"}),
        explanation="Tomcat or phone trust certificate is expired or invalid.",
        next_best_action="Renew Tomcat certificate and update CTL/ITL on affected phones.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-SIP-TRUNK",
        title=HYP_SIP_TRUNK,
        confidence=89.0,
        required_signals=frozenset({"sip_trunk_down"}),
        supporting_signals=frozenset({"sip_trunk_down"}),
        explanation="CUCM SIP trunk is down or unreachable.",
        next_best_action="Verify trunk destination, security profile, and provider status.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-ROUTE",
        title=HYP_ROUTING,
        confidence=84.0,
        required_signals=frozenset({"route_pattern_missing"}),
        supporting_signals=frozenset({"route_pattern_missing", "route_group_unavailable"}),
        explanation="Route plan analysis shows missing route pattern or unavailable route group.",
        next_best_action="Review route pattern, route list, and route group membership.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-CSS",
        title=HYP_CSS_MISMATCH,
        confidence=83.0,
        required_signals=frozenset({"css_missing"}),
        supporting_signals=frozenset({"css_missing", "css_partition_mismatch"}),
        explanation="Device CSS does not provide access to required partition.",
        next_best_action="Add partition to CSS or assign correct CSS to device line.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-PARTITION",
        title=HYP_PARTITION_MISMATCH,
        confidence=82.0,
        required_signals=frozenset({"partition_missing"}),
        supporting_signals=frozenset({"partition_missing"}),
        explanation="Required partition is missing from calling search space.",
        next_best_action="Review CSS membership and partition access for failing destination.",
    ),
    HypothesisRule(
        rule_id="HYP-CUCM-MEDIA",
        title=HYP_MEDIA_RESOURCE,
        confidence=80.0,
        required_signals=frozenset({"media_resource_unavailable"}),
        supporting_signals=frozenset({"media_resource_unavailable", "missing_mtp", "missing_transcoder"}),
        explanation="Required MTP, transcoder, or MRGL resource is unavailable.",
        next_best_action="Audit MRGL assignment and restore media resource devices.",
    ),
)

VP_CUCM_0001_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    CorrelationRule(
        rule_id="replication_phone_registration",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"db_replication_unhealthy", "phone_not_registered"}),
        hypothesis_title=HYP_DB_REPLICATION,
        confidence_delta=8.0,
        explanation="Unhealthy DB replication with phone registration failures points to replication root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="callmanager_registration_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"callmanager_service_stopped", "phone_not_registered"}),
        hypothesis_title=HYP_CALLMANAGER_SERVICE,
        confidence_delta=10.0,
        explanation="CallManager service down correlates with registration failures on affected node.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="css_routing_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"css_missing", "route_pattern_missing"}),
        hypothesis_title=HYP_CSS_MISMATCH,
        confidence_delta=6.0,
        explanation="CSS restriction with missing route pattern reinforces routing failure.",
    ),
    CorrelationRule(
        rule_id="partition_routing_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"partition_missing", "route_pattern_missing"}),
        hypothesis_title=HYP_PARTITION_MISMATCH,
        confidence_delta=6.0,
        explanation="Partition mismatch with route plan gap reinforces routing failure.",
    ),
    CorrelationRule(
        rule_id="certificate_tls_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"certificate_expired", "tls_handshake_failed"}),
        hypothesis_title=HYP_CERTIFICATE,
        confidence_delta=8.0,
        explanation="Expired certificate with TLS handshake failure reinforces certificate root cause.",
        apply_max_cap=True,
    ),
)

VP_CUCM_0001_ACTION_PLANS: dict[str, HypothesisActionPlan] = {
    "HYP-CUCM-PHONE-REG": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-CISCO-CUCM-RB-001 phone registration runbook",
            "Verify device pool, CM group, and network reachability",
        ),
        verification_steps=(
            "Execute VP-CISCO-CUCM-VG-001 RIS verification guide",
            "Confirm phones show Registered in RIS",
        ),
        rollback_guidance=("Restore previous CM group and device pool assignment from change record",),
        command="show risdb query phone",
    ),
    "HYP-CUCM-DB-REP": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-CISCO-CUCM-RB-005 cluster replication runbook",
            "Resolve network and NTP issues between cluster nodes",
        ),
        verification_steps=("Execute VP-CISCO-CUCM-VG-004 database replication verification guide",),
        command="utils dbreplication runtimestate",
        requires_engineer_approval=True,
    ),
    "HYP-CUCM-CM-SVC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-CISCO-CUCM-RB-005 cluster service recovery runbook",
            "Restart Cisco CallManager on affected node",
        ),
        verification_steps=("Execute VP-CISCO-CUCM-VG-010 critical services verification guide",),
        command="utils service list",
        requires_engineer_approval=True,
    ),
    "HYP-CUCM-TFTP": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-004 TFTP runbook", "Start Cisco TFTP service"),
        verification_steps=("Execute VP-CISCO-CUCM-VG-003 TFTP verification guide",),
        command="utils service list",
    ),
    "HYP-CUCM-CERT": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-009 certificate runbook", "Renew Tomcat certificates"),
        verification_steps=("Execute VP-CISCO-CUCM-VG-005 certificate verification guide",),
        command="show cert list",
        requires_engineer_approval=True,
    ),
    "HYP-CUCM-SIP-TRUNK": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-002 SIP trunk runbook", "Verify trunk and provider status"),
        verification_steps=("Execute VP-CISCO-CUCM-VG-002 SIP trunk verification guide",),
        command="show sip trunk",
    ),
    "HYP-CUCM-ROUTE": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-010 route pattern runbook",),
        verification_steps=("Execute VP-CISCO-CUCM-VG-009 routing verification guide",),
        command="show route plan",
    ),
    "HYP-CUCM-CSS": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-003 CSS runbook",),
        verification_steps=("Execute VP-CISCO-CUCM-VG-008 CSS verification guide",),
    ),
    "HYP-CUCM-PARTITION": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-003 CSS and partition runbook",),
        verification_steps=("Execute VP-CISCO-CUCM-VG-008 CSS verification guide",),
    ),
    "HYP-CUCM-MEDIA": HypothesisActionPlan(
        recommended_actions=("Follow VP-CISCO-CUCM-RB-006 MTP/media runbook",),
        verification_steps=("Execute VP-CISCO-CUCM-VG-006 media verification guide",),
    ),
}
