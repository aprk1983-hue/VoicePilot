"""AudioCodes SBC investigation constants and deterministic engine rules."""

from __future__ import annotations

from runtime.correlation_engine import CorrelationRule, CORRELATION_TYPE_REINFORCEMENT
from runtime.hypothesis_engine import HypothesisRule
from runtime.recommendation_engine import HypothesisActionPlan

VP_AUDIOCODES_0001_PLAYBOOK_ID = "VP-AUDIOCODES-0001"

AUDIOCODES_INTAKE_ANSWERS = [
    "yes",
    "2026-06-19",
    "sip trunk outbound call failure",
    "all destinations",
    "provider sip trunk",
    "no",
]

AUDIOCODES_EVIDENCE_FILES: tuple[tuple[str, str], ...] = (
    ("show voip status", "show_voip_status.txt"),
    ("show sip-options", "show_sip_options.txt"),
    ("show proxy-set", "show_proxy_set.txt"),
    ("show ip-group", "show_ip_group.txt"),
    ("show routing-table", "show_routing_table.txt"),
    ("show media-realm", "show_media_realm.txt"),
    ("show tls-context", "show_tls_context.txt"),
    ("show certificates", "show_certificates.txt"),
    ("show ha-status", "show_ha_status.txt"),
    ("show licenses", "show_licenses.txt"),
)

AUDIOCODES_ALL_FAIL_EVIDENCE = [command for command, _ in AUDIOCODES_EVIDENCE_FILES]

# Hypothesis titles
HYP_PROVIDER_UNAVAILABLE = "Provider SIP service unavailable"
HYP_SIP_OPTIONS = "SIP OPTIONS failure"
HYP_PROXY_SET = "Proxy Set unavailable"
HYP_IP_GROUP = "IP Group disabled"
HYP_ROUTING = "Routing configuration issue"
HYP_TLS_CERTIFICATE = "TLS certificate expired"
HYP_TLS_NEGOTIATION = "TLS negotiation failure"
HYP_MEDIA_REALM = "Media Realm failure"
HYP_RTP_PATH = "RTP path issue"
HYP_ONE_WAY_AUDIO = "One-way audio"
HYP_CODEC = "Codec negotiation issue"
HYP_LICENSE = "License exhaustion"
HYP_HA_SYNC = "HA synchronization issue"
HYP_GATEWAY = "Gateway unreachable"
HYP_DNS = "DNS resolution failure"

VP_AUDIOCODES_0001_RULES: tuple[HypothesisRule, ...] = (
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-PROVIDER",
        title=HYP_PROVIDER_UNAVAILABLE,
        confidence=90.0,
        required_signals=frozenset({"provider_503"}),
        supporting_signals=frozenset({"provider_503", "sip_options_failure"}),
        explanation="Provider SIP service returned 503 Service Unavailable.",
        next_best_action="Validate provider outage and failover routing per VP-AUDIOCODES-SBC-RB-008.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-SIP-OPTIONS",
        title=HYP_SIP_OPTIONS,
        confidence=89.0,
        required_signals=frozenset({"sip_options_failure"}),
        supporting_signals=frozenset({"sip_options_failure", "provider_503"}),
        explanation="SIP OPTIONS health check to the provider is failing.",
        next_best_action="Inspect show sip-options and restore provider keepalive per VP-AUDIOCODES-SBC-RB-001.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-PROXY",
        title=HYP_PROXY_SET,
        confidence=92.0,
        required_signals=frozenset({"proxy_set_unavailable"}),
        supporting_signals=frozenset({"proxy_set_unavailable", "gateway_unreachable"}),
        explanation="Proxy Set is unavailable or inactive.",
        next_best_action="Validate proxy set state per VP-AUDIOCODES-SBC-RB-003.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-IP-GROUP",
        title=HYP_IP_GROUP,
        confidence=93.0,
        required_signals=frozenset({"ip_group_disabled"}),
        supporting_signals=frozenset({"ip_group_disabled", "routing_table_issue"}),
        explanation="IP Group is administratively disabled.",
        next_best_action="Review IP Group configuration per VP-AUDIOCODES-SBC-RB-003.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-ROUTING",
        title=HYP_ROUTING,
        confidence=91.0,
        required_signals=frozenset({"routing_table_issue"}),
        supporting_signals=frozenset({"routing_table_issue", "ip_group_disabled"}),
        explanation="Routing table is missing destination or IP Group assignment.",
        next_best_action="Repair routing table entries per VP-AUDIOCODES-SBC-RB-004.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-TLS-CERT",
        title=HYP_TLS_CERTIFICATE,
        confidence=95.0,
        required_signals=frozenset({"tls_certificate_expired"}),
        supporting_signals=frozenset({"tls_certificate_expired", "tls_negotiation_failure"}),
        explanation="TLS certificate on the SBC is expired or invalid.",
        next_best_action="Renew TLS certificate per VP-AUDIOCODES-SBC-RB-002.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-TLS-NEG",
        title=HYP_TLS_NEGOTIATION,
        confidence=92.0,
        required_signals=frozenset({"tls_negotiation_failure"}),
        supporting_signals=frozenset({"tls_negotiation_failure", "tls_certificate_expired"}),
        explanation="TLS handshake negotiation is failing on the SBC.",
        next_best_action="Validate TLS context and cipher suite per VP-AUDIOCODES-SBC-RB-002.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-MEDIA-REALM",
        title=HYP_MEDIA_REALM,
        confidence=92.0,
        required_signals=frozenset({"media_realm_failure"}),
        supporting_signals=frozenset({"media_realm_failure", "rtp_one_way_audio"}),
        explanation="Media Realm is down or inactive.",
        next_best_action="Restore media realm per VP-AUDIOCODES-SBC-RB-005.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-RTP",
        title=HYP_RTP_PATH,
        confidence=89.0,
        required_signals=frozenset({"rtp_one_way_audio", "gateway_unreachable"}),
        supporting_signals=frozenset({"rtp_one_way_audio", "media_realm_failure"}),
        explanation="RTP media path is impaired between SBC and provider.",
        next_best_action="Validate RTP path and firewall pinholes per VP-AUDIOCODES-SBC-RB-005.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-ONEWAY",
        title=HYP_ONE_WAY_AUDIO,
        confidence=88.0,
        required_signals=frozenset({"rtp_one_way_audio"}),
        supporting_signals=frozenset({"rtp_one_way_audio", "media_realm_failure"}),
        explanation="One-way audio detected due to missing or invalid media IP.",
        next_best_action="Validate media realm IP addressing per VP-AUDIOCODES-SBC-RB-005.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-CODEC",
        title=HYP_CODEC,
        confidence=87.0,
        required_signals=frozenset({"srtp_mismatch"}),
        supporting_signals=frozenset({"srtp_mismatch", "codec_mismatch_488"}),
        explanation="Codec or SRTP negotiation mismatch between endpoints.",
        next_best_action="Align codec and SRTP profiles per VP-AUDIOCODES-SBC-RB-005.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-LICENSE",
        title=HYP_LICENSE,
        confidence=94.0,
        required_signals=frozenset({"session_license_exhausted"}),
        supporting_signals=frozenset({"session_license_exhausted", "call_failure_spike"}),
        explanation="Session license capacity is exhausted on the SBC.",
        next_best_action="Review license utilization per VP-AUDIOCODES-SBC-RB-009.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-HA-SYNC",
        title=HYP_HA_SYNC,
        confidence=91.0,
        required_signals=frozenset({"standby_synchronization_failure"}),
        supporting_signals=frozenset({"standby_synchronization_failure", "ha_failover"}),
        explanation="HA standby node is out of synchronization.",
        next_best_action="Restore HA synchronization per VP-AUDIOCODES-SBC-RB-006.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-GATEWAY",
        title=HYP_GATEWAY,
        confidence=88.0,
        required_signals=frozenset({"gateway_unreachable"}),
        supporting_signals=frozenset({"gateway_unreachable", "dns_resolution_failure"}),
        explanation="Provider gateway address is missing or unreachable.",
        next_best_action="Validate proxy address and connectivity per VP-AUDIOCODES-SBC-RB-008.",
    ),
    HypothesisRule(
        rule_id="HYP-AUDIOCODES-DNS",
        title=HYP_DNS,
        confidence=86.0,
        required_signals=frozenset({"dns_resolution_failure"}),
        supporting_signals=frozenset({"dns_resolution_failure", "gateway_unreachable"}),
        explanation="DNS resolution for provider FQDN is failing.",
        next_best_action="Validate DNS resolution per VP-AUDIOCODES-SBC-RB-010.",
    ),
)

VP_AUDIOCODES_0001_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    CorrelationRule(
        rule_id="audiocodes_sip_options_provider_503",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"sip_options_failure", "provider_503"}),
        hypothesis_title=HYP_PROVIDER_UNAVAILABLE,
        confidence_delta=8.0,
        explanation="SIP OPTIONS failure with provider 503 reinforces provider outage.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="audiocodes_tls_expired_negotiation",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"tls_certificate_expired", "tls_negotiation_failure"}),
        hypothesis_title=HYP_TLS_CERTIFICATE,
        confidence_delta=9.0,
        explanation="Expired TLS certificate with negotiation failure reinforces certificate root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="audiocodes_ip_group_routing",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"ip_group_disabled", "routing_table_issue"}),
        hypothesis_title=HYP_ROUTING,
        confidence_delta=7.0,
        explanation="Disabled IP Group with routing failure reinforces routing configuration issue.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="audiocodes_media_realm_rtp",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"media_realm_failure", "rtp_one_way_audio"}),
        hypothesis_title=HYP_MEDIA_REALM,
        confidence_delta=8.0,
        explanation="Media Realm failure with one-way audio reinforces media infrastructure issue.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="audiocodes_license_call_failures",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"session_license_exhausted", "call_failure_spike"}),
        hypothesis_title=HYP_LICENSE,
        confidence_delta=7.0,
        explanation="License exhaustion with elevated call failures reinforces capacity issue.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="audiocodes_ha_sync_failover",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"standby_synchronization_failure", "ha_failover"}),
        hypothesis_title=HYP_HA_SYNC,
        confidence_delta=8.0,
        explanation="HA sync failure with standby active reinforces HA degradation.",
        apply_max_cap=True,
    ),
)

VP_AUDIOCODES_0001_ACTION_PLANS: dict[str, HypothesisActionPlan] = {
    "HYP-AUDIOCODES-PROVIDER": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-008 provider validation runbook",
            "Confirm provider outage and engage carrier NOC",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-008 provider verification guide",),
        rollback_guidance=("Fail over to secondary provider trunk if configured",),
        command="show sip-options",
    ),
    "HYP-AUDIOCODES-SIP-OPTIONS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-001 SIP trunk validation runbook",
            "Restore SIP OPTIONS keepalive response on provider path",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-001 SIP trunk verification guide",),
        command="show sip-options",
    ),
    "HYP-AUDIOCODES-PROXY": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-003 proxy and IP group validation runbook",
            "Restore Proxy Set availability and heartbeat",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-003 proxy verification guide",),
        command="show proxy-set",
    ),
    "HYP-AUDIOCODES-IP-GROUP": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-003 proxy and IP group validation runbook",
            "Enable IP Group and validate proxy set association",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-003 proxy verification guide",),
        command="show ip-group",
    ),
    "HYP-AUDIOCODES-ROUTING": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-004 routing validation runbook",
            "Repair routing table destination and IP Group mapping",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-004 routing verification guide",),
        command="show routing-table",
    ),
    "HYP-AUDIOCODES-TLS-CERT": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-002 TLS validation runbook",
            "Renew expired TLS certificate and validate chain",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-002 TLS verification guide",),
        command="show certificates",
        requires_engineer_approval=True,
    ),
    "HYP-AUDIOCODES-TLS-NEG": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-002 TLS validation runbook",
            "Align TLS context cipher suite and certificate binding",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-002 TLS verification guide",),
        command="show tls-context",
        requires_engineer_approval=True,
    ),
    "HYP-AUDIOCODES-MEDIA-REALM": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-005 media validation runbook",
            "Restore Media Realm state and RTP port range",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-005 media verification guide",),
        command="show media-realm",
    ),
    "HYP-AUDIOCODES-RTP": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-005 media validation runbook",
            "Validate RTP path, NAT, and firewall pinholes",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-005 media verification guide",),
        command="show media-realm",
    ),
    "HYP-AUDIOCODES-ONEWAY": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-005 media validation runbook",
            "Correct media IP addressing and symmetric RTP path",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-005 media verification guide",),
        command="show media-realm",
    ),
    "HYP-AUDIOCODES-CODEC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-005 media validation runbook",
            "Align codec list and SRTP mode across IP profiles",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-005 media verification guide",),
        command="show tls-context",
    ),
    "HYP-AUDIOCODES-LICENSE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-009 licensing validation runbook",
            "Increase session license capacity or reduce concurrent calls",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-009 licensing verification guide",),
        command="show licenses",
        requires_engineer_approval=True,
    ),
    "HYP-AUDIOCODES-HA-SYNC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-006 HA validation runbook",
            "Restore standby synchronization and validate cluster state",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-006 HA verification guide",),
        command="show ha-status",
        requires_engineer_approval=True,
    ),
    "HYP-AUDIOCODES-GATEWAY": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-008 provider validation runbook",
            "Restore provider gateway address and connectivity",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-008 provider verification guide",),
        command="show proxy-set",
    ),
    "HYP-AUDIOCODES-DNS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-AUDIOCODES-SBC-RB-010 DNS and capacity validation runbook",
            "Restore DNS resolution for provider FQDN",
        ),
        verification_steps=("Execute VP-AUDIOCODES-SBC-VG-010 DNS verification guide",),
        command="show voip status",
    ),
}
