"""Genesys Cloud investigation constants and deterministic engine rules."""

from __future__ import annotations

from runtime.correlation_engine import CorrelationRule, CORRELATION_TYPE_REINFORCEMENT
from runtime.hypothesis_engine import HypothesisRule
from runtime.recommendation_engine import HypothesisActionPlan

VP_GENESYS_0001_PLAYBOOK_ID = "VP-GENESYS-0001"

GENESYS_INTAKE_ANSWERS = [
    "yes",
    "2026-06-19",
    "genesys cloud contact center routing failure",
    "all queues and agents",
    "byoc cloud trunk",
    "no",
]

GENESYS_EVIDENCE_FILES: tuple[tuple[str, str], ...] = (
    ("organization-export", "organization_export.csv"),
    ("users-export", "users_export.json"),
    ("queues-export", "queues_export.csv"),
    ("queue-members-export", "queue_members_export.csv"),
    ("agents-export", "agents_export.txt"),
    ("presence-export", "presence_export.yaml"),
    ("flows-export", "flows_export.csv"),
    ("architect-export", "architect_export.json"),
    ("data-actions-export", "data_actions_export.csv"),
    ("byoc-cloud-trunks-export", "byoc_cloud_trunks_export.txt"),
    ("byoc-premises-trunks-export", "byoc_premises_trunks_export.csv"),
    ("edge-devices-export", "edge_devices_export.json"),
    ("recording-policies-export", "recording_policies_export.yaml"),
    ("campaigns-export", "campaigns_export.csv"),
    ("skills-export", "skills_export.json"),
)

GENESYS_ALL_FAIL_EVIDENCE = [command for command, _ in GENESYS_EVIDENCE_FILES]

HYP_OAUTH = "OAuth failure"
HYP_TOKEN = "Token expired"
HYP_ORG = "Organization unavailable"
HYP_EDGE_OFFLINE = "Edge offline"
HYP_EDGE_DEGRADED = "Edge degraded"
HYP_CONVERSATION = "Conversation service unavailable"
HYP_ANALYTICS = "Analytics service unavailable"
HYP_BYOC_CLOUD = "BYOC Cloud trunk unavailable"
HYP_BYOC_PREMISES = "BYOC Premises Edge unavailable"
HYP_SIP_OPTIONS = "SIP OPTIONS failure"
HYP_CARRIER = "Carrier unreachable"
HYP_TLS_CERT = "TLS certificate expired"
HYP_TLS_NEG = "TLS negotiation failure"
HYP_QUEUE = "Queue unavailable"
HYP_QUEUE_MEMBER = "Queue member unavailable"
HYP_QUEUE_OVERLOAD = "Queue overloaded"
HYP_AGENT_LOGIN = "Agent not logged in"
HYP_AGENT_STUCK = "Agent stuck interacting"
HYP_PRESENCE_SYNC = "Presence synchronization issue"
HYP_USER_ROUTING = "User routing disabled"
HYP_FLOW = "Architect flow failure"
HYP_ARCHITECT_PUBLISH = "Architect publish issue"
HYP_DATA_ACTION = "Data Action failure"
HYP_WEBRTC = "WebRTC failure"
HYP_MEDIA = "Media service unavailable"
HYP_RECORDING = "Recording failure"
HYP_CAMPAIGN = "Outbound campaign failure"

VP_GENESYS_0001_RULES: tuple[HypothesisRule, ...] = (
    HypothesisRule(
        rule_id="HYP-GENESYS-OAUTH",
        title="OAuth failure",
        confidence=94.0,
        required_signals=frozenset({"oauth_failure"}),
        supporting_signals=frozenset({"oauth_failure"}),
        explanation="OAuth failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-001 and VP-GENESYS-CLOUD-VG-001 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-TOKEN",
        title="Token expired",
        confidence=92.0,
        required_signals=frozenset({"token_expired"}),
        supporting_signals=frozenset({"token_expired"}),
        explanation="Token expired detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-001 and VP-GENESYS-CLOUD-VG-001 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-ORG",
        title="Organization unavailable",
        confidence=95.0,
        required_signals=frozenset({"organization_unavailable"}),
        supporting_signals=frozenset({"organization_unavailable"}),
        explanation="Organization unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-002 and VP-GENESYS-CLOUD-VG-002 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-EDGE-OFFLINE",
        title="Edge offline",
        confidence=93.0,
        required_signals=frozenset({"edge_offline"}),
        supporting_signals=frozenset({"edge_offline"}),
        explanation="Edge offline detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-002 and VP-GENESYS-CLOUD-VG-002 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-EDGE-DEGRADED",
        title="Edge degraded",
        confidence=88.0,
        required_signals=frozenset({"edge_degraded"}),
        supporting_signals=frozenset({"edge_degraded"}),
        explanation="Edge degraded detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-002 and VP-GENESYS-CLOUD-VG-002 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-CONVERSATION",
        title="Conversation service unavailable",
        confidence=91.0,
        required_signals=frozenset({"conversation_service_unavailable"}),
        supporting_signals=frozenset({"conversation_service_unavailable"}),
        explanation="Conversation service unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-009 and VP-GENESYS-CLOUD-VG-009 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-ANALYTICS",
        title="Analytics service unavailable",
        confidence=86.0,
        required_signals=frozenset({"analytics_service_unavailable"}),
        supporting_signals=frozenset({"analytics_service_unavailable"}),
        explanation="Analytics service unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-009 and VP-GENESYS-CLOUD-VG-009 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-BYOC-CLOUD",
        title="BYOC Cloud trunk unavailable",
        confidence=93.0,
        required_signals=frozenset({"byoc_cloud_trunk_failure"}),
        supporting_signals=frozenset({"byoc_cloud_trunk_failure"}),
        explanation="BYOC Cloud trunk unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-003 and VP-GENESYS-CLOUD-VG-003 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-BYOC-PREMISES",
        title="BYOC Premises Edge unavailable",
        confidence=92.0,
        required_signals=frozenset({"byoc_premises_edge_unavailable"}),
        supporting_signals=frozenset({"byoc_premises_edge_unavailable"}),
        explanation="BYOC Premises Edge unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-010 and VP-GENESYS-CLOUD-VG-010 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-SIP-OPTIONS",
        title="SIP OPTIONS failure",
        confidence=89.0,
        required_signals=frozenset({"sip_options_failure"}),
        supporting_signals=frozenset({"sip_options_failure"}),
        explanation="SIP OPTIONS failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-003 and VP-GENESYS-CLOUD-VG-003 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-CARRIER",
        title="Carrier unreachable",
        confidence=90.0,
        required_signals=frozenset({"carrier_unreachable"}),
        supporting_signals=frozenset({"carrier_unreachable"}),
        explanation="Carrier unreachable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-003 and VP-GENESYS-CLOUD-VG-003 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-TLS-CERT",
        title="TLS certificate expired",
        confidence=95.0,
        required_signals=frozenset({"tls_certificate_expired"}),
        supporting_signals=frozenset({"tls_certificate_expired"}),
        explanation="TLS certificate expired detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-004 and VP-GENESYS-CLOUD-VG-004 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-TLS-NEG",
        title="TLS negotiation failure",
        confidence=92.0,
        required_signals=frozenset({"tls_negotiation_failure"}),
        supporting_signals=frozenset({"tls_negotiation_failure"}),
        explanation="TLS negotiation failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-004 and VP-GENESYS-CLOUD-VG-004 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-QUEUE",
        title="Queue unavailable",
        confidence=92.0,
        required_signals=frozenset({"queue_unavailable"}),
        supporting_signals=frozenset({"queue_unavailable"}),
        explanation="Queue unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-005 and VP-GENESYS-CLOUD-VG-005 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-QUEUE-MEMBER",
        title="Queue member unavailable",
        confidence=91.0,
        required_signals=frozenset({"queue_member_unavailable"}),
        supporting_signals=frozenset({"queue_member_unavailable"}),
        explanation="Queue member unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-005 and VP-GENESYS-CLOUD-VG-005 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-QUEUE-OVERLOAD",
        title="Queue overloaded",
        confidence=88.0,
        required_signals=frozenset({"queue_overloaded"}),
        supporting_signals=frozenset({"queue_overloaded"}),
        explanation="Queue overloaded detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-005 and VP-GENESYS-CLOUD-VG-005 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-AGENT-LOGIN",
        title="Agent not logged in",
        confidence=90.0,
        required_signals=frozenset({"agent_not_logged_in"}),
        supporting_signals=frozenset({"agent_not_logged_in"}),
        explanation="Agent not logged in detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-006 and VP-GENESYS-CLOUD-VG-006 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-AGENT-STUCK",
        title="Agent stuck interacting",
        confidence=91.0,
        required_signals=frozenset({"agent_stuck_interacting"}),
        supporting_signals=frozenset({"agent_stuck_interacting"}),
        explanation="Agent stuck interacting detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-006 and VP-GENESYS-CLOUD-VG-006 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-PRESENCE-SYNC",
        title="Presence synchronization issue",
        confidence=89.0,
        required_signals=frozenset({"presence_synchronization_failure"}),
        supporting_signals=frozenset({"presence_synchronization_failure"}),
        explanation="Presence synchronization issue detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-006 and VP-GENESYS-CLOUD-VG-006 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-USER-ROUTING",
        title="User routing disabled",
        confidence=88.0,
        required_signals=frozenset({"user_routing_disabled"}),
        supporting_signals=frozenset({"user_routing_disabled"}),
        explanation="User routing disabled detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-006 and VP-GENESYS-CLOUD-VG-006 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-FLOW",
        title="Architect flow failure",
        confidence=91.0,
        required_signals=frozenset({"call_flow_failure"}),
        supporting_signals=frozenset({"call_flow_failure"}),
        explanation="Architect flow failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-007 and VP-GENESYS-CLOUD-VG-007 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-ARCHITECT-PUBLISH",
        title="Architect publish issue",
        confidence=92.0,
        required_signals=frozenset({"architect_publish_failure"}),
        supporting_signals=frozenset({"architect_publish_failure"}),
        explanation="Architect publish issue detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-007 and VP-GENESYS-CLOUD-VG-007 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-DATA-ACTION",
        title="Data Action failure",
        confidence=91.0,
        required_signals=frozenset({"data_action_failure"}),
        supporting_signals=frozenset({"data_action_failure"}),
        explanation="Data Action failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-007 and VP-GENESYS-CLOUD-VG-007 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-WEBRTC",
        title="WebRTC failure",
        confidence=90.0,
        required_signals=frozenset({"webrtc_failure"}),
        supporting_signals=frozenset({"webrtc_failure"}),
        explanation="WebRTC failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-008 and VP-GENESYS-CLOUD-VG-008 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-MEDIA",
        title="Media service unavailable",
        confidence=91.0,
        required_signals=frozenset({"media_service_unavailable"}),
        supporting_signals=frozenset({"media_service_unavailable"}),
        explanation="Media service unavailable detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-008 and VP-GENESYS-CLOUD-VG-008 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-RECORDING",
        title="Recording failure",
        confidence=90.0,
        required_signals=frozenset({"recording_failure"}),
        supporting_signals=frozenset({"recording_failure"}),
        explanation="Recording failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-009 and VP-GENESYS-CLOUD-VG-009 for advisory validation.",
    ),
    HypothesisRule(
        rule_id="HYP-GENESYS-CAMPAIGN",
        title="Outbound campaign failure",
        confidence=91.0,
        required_signals=frozenset({"outbound_campaign_failure"}),
        supporting_signals=frozenset({"outbound_campaign_failure"}),
        explanation="Outbound campaign failure detected from Genesys Cloud export evidence.",
        next_best_action="Follow VP-GENESYS-CLOUD-RB-010 and VP-GENESYS-CLOUD-VG-010 for advisory validation.",
    ),
)

VP_GENESYS_0001_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    CorrelationRule(
        rule_id="genesys_oauth_token",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"oauth_failure", "token_expired"}),
        hypothesis_title="OAuth failure",
        confidence_delta=9.0,
        explanation="OAuth failure with expired token reinforces authentication root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_edge_byoc_premises",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"byoc_premises_edge_unavailable", "edge_offline"}),
        hypothesis_title="BYOC Premises Edge unavailable",
        confidence_delta=8.0,
        explanation="Edge offline with BYOC Premises trunk failure reinforces edge infrastructure root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_byoc_sip_options",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"byoc_cloud_trunk_failure", "sip_options_failure"}),
        hypothesis_title="BYOC Cloud trunk unavailable",
        confidence_delta=8.0,
        explanation="BYOC trunk failure with SIP OPTIONS failure reinforces trunk/carrier root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_tls_expired_negotiation",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"tls_certificate_expired", "tls_negotiation_failure"}),
        hypothesis_title="TLS certificate expired",
        confidence_delta=9.0,
        explanation="Expired certificate with TLS negotiation failure reinforces TLS root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_queue_member_staffing",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"queue_member_unavailable", "queue_unavailable"}),
        hypothesis_title="Queue unavailable",
        confidence_delta=7.0,
        explanation="Queue unavailable with member unavailable reinforces queue staffing root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_agent_presence",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"agent_not_logged_in", "presence_synchronization_failure"}),
        hypothesis_title="Agent not logged in",
        confidence_delta=7.0,
        explanation="Agent not logged in with presence sync failure reinforces agent availability root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_architect_publish_flow",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"architect_publish_failure", "call_flow_failure"}),
        hypothesis_title="Architect flow failure",
        confidence_delta=8.0,
        explanation="Architect publish failure with flow failure reinforces Architect flow root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_data_action_flow",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"call_flow_failure", "data_action_failure"}),
        hypothesis_title="Data Action failure",
        confidence_delta=7.0,
        explanation="Data Action failure with flow failure reinforces integration root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_media_webrtc",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"media_service_unavailable", "webrtc_failure"}),
        hypothesis_title="Media service unavailable",
        confidence_delta=8.0,
        explanation="Media service unavailable with WebRTC failure reinforces media infrastructure root cause.",
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="genesys_carrier_sip_options",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset({"carrier_unreachable", "sip_options_failure"}),
        hypothesis_title="Carrier unreachable",
        confidence_delta=7.0,
        explanation="Carrier unreachable with SIP OPTIONS failure reinforces trunk path root cause.",
        apply_max_cap=True,
    ),
)

VP_GENESYS_0001_ACTION_PLANS: dict[str, HypothesisActionPlan] = {
    "HYP-GENESYS-OAUTH": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-001 advisory runbook",
            "Review Genesys Cloud export evidence for oauth failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-001 verification guide",
        ),
        command="organization-export",
        requires_engineer_approval=True,
    ),
    "HYP-GENESYS-TOKEN": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-001 advisory runbook",
            "Review Genesys Cloud export evidence for token expired",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-001 verification guide",
        ),
        command="organization-export",
        requires_engineer_approval=True,
    ),
    "HYP-GENESYS-ORG": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-002 advisory runbook",
            "Review Genesys Cloud export evidence for organization unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-002 verification guide",
        ),
        command="organization-export",
    ),
    "HYP-GENESYS-EDGE-OFFLINE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-002 advisory runbook",
            "Review Genesys Cloud export evidence for edge offline",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-002 verification guide",
        ),
        command="edge-devices-export",
    ),
    "HYP-GENESYS-EDGE-DEGRADED": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-002 advisory runbook",
            "Review Genesys Cloud export evidence for edge degraded",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-002 verification guide",
        ),
        command="edge-devices-export",
    ),
    "HYP-GENESYS-CONVERSATION": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-009 advisory runbook",
            "Review Genesys Cloud export evidence for conversation service unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-009 verification guide",
        ),
        command="organization-export",
    ),
    "HYP-GENESYS-ANALYTICS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-009 advisory runbook",
            "Review Genesys Cloud export evidence for analytics service unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-009 verification guide",
        ),
        command="organization-export",
    ),
    "HYP-GENESYS-BYOC-CLOUD": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-003 advisory runbook",
            "Review Genesys Cloud export evidence for byoc cloud trunk unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-003 verification guide",
        ),
        command="byoc-cloud-trunks-export",
    ),
    "HYP-GENESYS-BYOC-PREMISES": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-010 advisory runbook",
            "Review Genesys Cloud export evidence for byoc premises edge unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-010 verification guide",
        ),
        command="byoc-premises-trunks-export",
    ),
    "HYP-GENESYS-SIP-OPTIONS": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-003 advisory runbook",
            "Review Genesys Cloud export evidence for sip options failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-003 verification guide",
        ),
        command="byoc-cloud-trunks-export",
    ),
    "HYP-GENESYS-CARRIER": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-003 advisory runbook",
            "Review Genesys Cloud export evidence for carrier unreachable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-003 verification guide",
        ),
        command="byoc-cloud-trunks-export",
    ),
    "HYP-GENESYS-TLS-CERT": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-004 advisory runbook",
            "Review Genesys Cloud export evidence for tls certificate expired",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-004 verification guide",
        ),
        command="byoc-cloud-trunks-export",
        requires_engineer_approval=True,
    ),
    "HYP-GENESYS-TLS-NEG": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-004 advisory runbook",
            "Review Genesys Cloud export evidence for tls negotiation failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-004 verification guide",
        ),
        command="byoc-cloud-trunks-export",
        requires_engineer_approval=True,
    ),
    "HYP-GENESYS-QUEUE": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-005 advisory runbook",
            "Review Genesys Cloud export evidence for queue unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-005 verification guide",
        ),
        command="queues-export",
    ),
    "HYP-GENESYS-QUEUE-MEMBER": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-005 advisory runbook",
            "Review Genesys Cloud export evidence for queue member unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-005 verification guide",
        ),
        command="queue-members-export",
    ),
    "HYP-GENESYS-QUEUE-OVERLOAD": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-005 advisory runbook",
            "Review Genesys Cloud export evidence for queue overloaded",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-005 verification guide",
        ),
        command="queues-export",
    ),
    "HYP-GENESYS-AGENT-LOGIN": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-006 advisory runbook",
            "Review Genesys Cloud export evidence for agent not logged in",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-006 verification guide",
        ),
        command="agents-export",
    ),
    "HYP-GENESYS-AGENT-STUCK": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-006 advisory runbook",
            "Review Genesys Cloud export evidence for agent stuck interacting",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-006 verification guide",
        ),
        command="agents-export",
    ),
    "HYP-GENESYS-PRESENCE-SYNC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-006 advisory runbook",
            "Review Genesys Cloud export evidence for presence synchronization issue",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-006 verification guide",
        ),
        command="presence-export",
    ),
    "HYP-GENESYS-USER-ROUTING": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-006 advisory runbook",
            "Review Genesys Cloud export evidence for user routing disabled",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-006 verification guide",
        ),
        command="presence-export",
    ),
    "HYP-GENESYS-FLOW": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-007 advisory runbook",
            "Review Genesys Cloud export evidence for architect flow failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-007 verification guide",
        ),
        command="flows-export",
    ),
    "HYP-GENESYS-ARCHITECT-PUBLISH": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-007 advisory runbook",
            "Review Genesys Cloud export evidence for architect publish issue",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-007 verification guide",
        ),
        command="architect-export",
    ),
    "HYP-GENESYS-DATA-ACTION": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-007 advisory runbook",
            "Review Genesys Cloud export evidence for data action failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-007 verification guide",
        ),
        command="data-actions-export",
    ),
    "HYP-GENESYS-WEBRTC": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-008 advisory runbook",
            "Review Genesys Cloud export evidence for webrtc failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-008 verification guide",
        ),
        command="organization-export",
    ),
    "HYP-GENESYS-MEDIA": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-008 advisory runbook",
            "Review Genesys Cloud export evidence for media service unavailable",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-008 verification guide",
        ),
        command="organization-export",
    ),
    "HYP-GENESYS-RECORDING": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-009 advisory runbook",
            "Review Genesys Cloud export evidence for recording failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-009 verification guide",
        ),
        command="recording-policies-export",
    ),
    "HYP-GENESYS-CAMPAIGN": HypothesisActionPlan(
        recommended_actions=(
            "Follow VP-GENESYS-CLOUD-RB-010 advisory runbook",
            "Review Genesys Cloud export evidence for outbound campaign failure",
        ),
        verification_steps=(
            "Execute VP-GENESYS-CLOUD-VG-010 verification guide",
        ),
        command="campaigns-export",
    ),
}
