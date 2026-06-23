"""Genesys Cloud health rules for GVOM."""

from __future__ import annotations

from dataclasses import dataclass

from health.health_categories import HealthCategory
from health.health_models import HealthResult, HealthStatus
from health.health_rule import HealthRule
from health.health_severity import HealthSeverity
from model.genesys_objects import (
    Agent,
    ArchitectFlow,
    ByocCloudTrunk,
    ByocPremisesTrunk,
    Campaign,
    DataAction,
    EdgeDevice,
    GenesysOrganization,
    PresenceDefinition,
    Queue,
    QueueMember,
    Recording,
    RecordingPolicy,
    SipEndpoint,
    UserRoutingStatus,
)
from model.voice_graph import (
    OBJECT_TYPE_GENESYS_AGENT,
    OBJECT_TYPE_GENESYS_ARCHITECT_FLOW,
    OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,
    OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK,
    OBJECT_TYPE_GENESYS_CAMPAIGN,
    OBJECT_TYPE_GENESYS_DATA_ACTION,
    OBJECT_TYPE_GENESYS_EDGE_DEVICE,
    OBJECT_TYPE_GENESYS_ORGANIZATION,
    OBJECT_TYPE_GENESYS_PRESENCE_DEFINITION,
    OBJECT_TYPE_GENESYS_QUEUE,
    OBJECT_TYPE_GENESYS_QUEUE_MEMBER,
    OBJECT_TYPE_GENESYS_RECORDING,
    OBJECT_TYPE_GENESYS_RECORDING_POLICY,
    OBJECT_TYPE_GENESYS_SIP_ENDPOINT,
    OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS,
    VoiceObject,
)
from model.voice_topology import VoiceTopology


_DOWN_STATES = frozenset({"down", "disabled", "inactive", "unavailable", "failed", "offline"})
_UNAVAILABLE_STATES = frozenset({"unavailable", "down", "inactive", "offline", "suspended"})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysOauthFailureRule(HealthRule):
    id: str = "genesys_oauth_failure"
    title: str = "OAuth authentication failure"
    description: str = "Genesys Cloud OAuth authentication must succeed for API access."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "oauth_failure", "genesys_oauth_failure"):
            return _fail(self, organization, "OAuth authentication failed.")
        auth_state = (_meta_text(organization, "oauth_status", "auth_status") or "").lower()
        if auth_state in {"failed", "failure", "unauthorized", "invalid_client"}:
            return _fail(self, organization, "OAuth authentication failed.")
        return _pass(self, organization, "OAuth authentication not reported as failed.")


@dataclass(frozen=True)
class GenesysTokenExpiredRule(HealthRule):
    id: str = "genesys_token_expired"
    title: str = "OAuth token expired"
    description: str = "Expired OAuth tokens block Genesys Cloud API operations."
    category: HealthCategory = HealthCategory.SECURITY
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "token_expired", "genesys_token_expired"):
            return _fail(self, organization, "OAuth token is expired.")
        token_state = (_meta_text(organization, "token_status", "oauth_token_status") or "").lower()
        if token_state in {"expired", "invalid", "revoked"}:
            return _fail(self, organization, "OAuth token is expired.")
        return _pass(self, organization, "OAuth token state not reported as expired.")


@dataclass(frozen=True)
class GenesysOrganizationUnavailableRule(HealthRule):
    id: str = "genesys_organization_unavailable"
    title: str = "Organization unavailable"
    description: str = "Genesys Cloud organization must be active."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "organization_unavailable") or _state_is_unavailable(
            organization.state
        ):
            return _fail(self, organization, "Organization is unavailable.")
        return _pass(self, organization, "Organization is available or state unknown.")


# ---------------------------------------------------------------------------
# Users / Agents
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysAgentNotLoggedInRule(HealthRule):
    id: str = "genesys_agent_not_logged_in"
    title: str = "Agent not logged in"
    description: str = "Agents must be logged in to receive queue interactions."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_AGENT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        agent = _require_type(obj, Agent)
        state = (agent.state or "").lower()
        if _meta_flag(agent, "agent_not_logged_in") or state in {
            "offline",
            "logged_out",
            "logged out",
            "not_logged_in",
        }:
            return _fail(self, agent, "Agent is not logged in.")
        return _pass(self, agent, "Agent login state not reported as offline.")


@dataclass(frozen=True)
class GenesysAgentStuckInteractingRule(HealthRule):
    id: str = "genesys_agent_stuck_interacting"
    title: str = "Agent stuck interacting"
    description: str = "Agents stuck interacting cannot accept new queue work."
    category: HealthCategory = HealthCategory.PERFORMANCE
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_AGENT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        agent = _require_type(obj, Agent)
        state = (agent.state or "").lower()
        if _meta_flag(agent, "agent_stuck_interacting") or state in {
            "interacting",
            "stuck_interacting",
            "stuck interacting",
        }:
            return _fail(self, agent, "Agent is stuck interacting.")
        return _pass(self, agent, "Agent is not reported as stuck interacting.")


@dataclass(frozen=True)
class GenesysPresenceSyncFailureRule(HealthRule):
    id: str = "genesys_presence_sync_failure"
    title: str = "Presence synchronization failure"
    description: str = "Presence definitions must remain synchronized with routing."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_GENESYS_PRESENCE_DEFINITION,
        OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, PresenceDefinition):
            sync = (_meta_text(obj, "sync_state", "synchronization") or "").lower()
            if _meta_flag(obj, "presence_synchronization_failure", "presence_sync_failure"):
                return _fail(self, obj, "Presence synchronization failed.")
            if sync in {"out_of_sync", "failed", "desynchronized"}:
                return _fail(self, obj, "Presence synchronization failed.")
            return _pass(self, obj, "Presence synchronization not reported as failed.")
        routing = _require_type(obj, UserRoutingStatus)
        sync = (_meta_text(routing, "sync_state", "presence_sync_state") or "").lower()
        if _meta_flag(routing, "presence_sync_failure"):
            return _fail(self, routing, "User presence synchronization failed.")
        if sync in {"out_of_sync", "failed", "desynchronized"}:
            return _fail(self, routing, "User presence synchronization failed.")
        return _pass(self, routing, "User presence synchronization not reported as failed.")


@dataclass(frozen=True)
class GenesysUserRoutingDisabledRule(HealthRule):
    id: str = "genesys_user_routing_disabled"
    title: str = "User routing disabled"
    description: str = "User routing status must allow queue routing."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        routing = _require_type(obj, UserRoutingStatus)
        status = (routing.routing_status or "").lower()
        if _meta_flag(routing, "user_routing_disabled") or status in {
            "disabled",
            "off_queue",
            "not_routing",
            "inactive",
        }:
            return _fail(self, routing, "User routing is disabled.")
        return _pass(self, routing, "User routing is enabled or state unknown.")


# ---------------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysQueueUnavailableRule(HealthRule):
    id: str = "genesys_queue_unavailable"
    title: str = "Queue unavailable"
    description: str = "ACD queues must be available for call distribution."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_QUEUE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        queue = _require_type(obj, Queue)
        if _meta_flag(queue, "queue_unavailable") or _state_is_unavailable(queue.state):
            return _fail(self, queue, "Queue is unavailable.")
        return _pass(self, queue, "Queue is available or state unknown.")


@dataclass(frozen=True)
class GenesysQueueNoMembersRule(HealthRule):
    id: str = "genesys_queue_no_members"
    title: str = "Queue has no members"
    description: str = "Queues require at least one active member for routing."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_QUEUE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        queue = _require_type(obj, Queue)
        if _meta_flag(queue, "queue_no_members"):
            return _fail(self, queue, "Queue has no members.")
        queue_ref = queue.queue_id or queue.name
        if not queue_ref:
            return _pass(self, queue, "Queue identity unavailable for member check.")
        members = [
            member
            for member in topology.genesys_queues
            if isinstance(member, QueueMember) and member.queue_id in {queue_ref, queue.queue_id}
        ]
        if not members:
            return _fail(self, queue, "Queue has no members.")
        return _pass(self, queue, f"{len(members)} queue member(s) configured.")


@dataclass(frozen=True)
class GenesysQueueMemberUnavailableRule(HealthRule):
    id: str = "genesys_queue_member_unavailable"
    title: str = "Queue member unavailable"
    description: str = "Queue members must be available for ACD routing."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_QUEUE_MEMBER,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        member = _require_type(obj, QueueMember)
        if _meta_flag(member, "queue_member_unavailable") or _state_is_unavailable(member.state):
            return _fail(self, member, "Queue member is unavailable.")
        return _pass(self, member, "Queue member is available or state unknown.")


@dataclass(frozen=True)
class GenesysQueueOverloadedRule(HealthRule):
    id: str = "genesys_queue_overloaded"
    title: str = "Queue overloaded"
    description: str = "Queue overload indicates insufficient agent capacity."
    category: HealthCategory = HealthCategory.PERFORMANCE
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_QUEUE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        queue = _require_type(obj, Queue)
        if _meta_flag(queue, "queue_overloaded"):
            return _fail(self, queue, "Queue is overloaded.")
        waiting = _meta_int(queue, "waiting_calls", "queue_depth", "offered_calls")
        threshold = _meta_int(queue, "queue_capacity_threshold", "capacity_threshold")
        if waiting is not None and threshold is not None and waiting >= threshold:
            return _fail(self, queue, "Queue is overloaded.")
        if waiting is not None and waiting >= 50:
            return _fail(self, queue, "Queue is overloaded.")
        return _pass(self, queue, "Queue load not reported as overloaded.")


# ---------------------------------------------------------------------------
# Voice Routing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysByocCloudUnavailableRule(HealthRule):
    id: str = "genesys_byoc_cloud_unavailable"
    title: str = "BYOC Cloud trunk unavailable"
    description: str = "BYOC Cloud trunks must be available for PSTN connectivity."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        trunk = _require_type(obj, ByocCloudTrunk)
        if _meta_flag(trunk, "byoc_cloud_trunk_failure", "byoc_cloud_unavailable"):
            return _fail(self, trunk, "BYOC Cloud trunk is unavailable.")
        if _state_is_unavailable(trunk.state):
            return _fail(self, trunk, "BYOC Cloud trunk is unavailable.")
        return _pass(self, trunk, "BYOC Cloud trunk is available or state unknown.")


@dataclass(frozen=True)
class GenesysByocPremisesUnavailableRule(HealthRule):
    id: str = "genesys_byoc_premises_unavailable"
    title: str = "BYOC Premises trunk unavailable"
    description: str = "BYOC Premises trunks must be available for Edge routing."
    category: HealthCategory = HealthCategory.PROVIDER
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        trunk = _require_type(obj, ByocPremisesTrunk)
        if _meta_flag(trunk, "byoc_premises_edge_unavailable", "byoc_premises_unavailable"):
            return _fail(self, trunk, "BYOC Premises trunk is unavailable.")
        if _state_is_unavailable(trunk.state):
            return _fail(self, trunk, "BYOC Premises trunk is unavailable.")
        return _pass(self, trunk, "BYOC Premises trunk is available or state unknown.")


@dataclass(frozen=True)
class GenesysSipOptionsFailureRule(HealthRule):
    id: str = "genesys_sip_options_failure"
    title: str = "SIP OPTIONS failure"
    description: str = "SIP OPTIONS keepalive must succeed for trunk health."
    category: HealthCategory = HealthCategory.SIP
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,
        OBJECT_TYPE_GENESYS_SIP_ENDPOINT,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, ByocCloudTrunk):
            status = (obj.sip_options_status or "").lower()
            if _meta_flag(obj, "sip_options_failure") or status in {"failed", "failure", "503"}:
                return _fail(self, obj, "SIP OPTIONS keepalive failed.")
            return _pass(self, obj, "SIP OPTIONS state not reported as failed.")
        endpoint = _require_type(obj, SipEndpoint)
        status = (_meta_text(endpoint, "sip_options_status", "options_status") or "").lower()
        if _meta_flag(endpoint, "sip_options_failure") or status in {"failed", "failure", "503"}:
            return _fail(self, endpoint, "SIP OPTIONS keepalive failed.")
        return _pass(self, endpoint, "SIP OPTIONS state not reported as failed.")


@dataclass(frozen=True)
class GenesysCarrierUnreachableRule(HealthRule):
    id: str = "genesys_carrier_unreachable"
    title: str = "Carrier unreachable"
    description: str = "Carrier endpoints must be reachable for PSTN calls."
    category: HealthCategory = HealthCategory.NETWORK
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,
        OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK,
        OBJECT_TYPE_GENESYS_SIP_ENDPOINT,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, ByocCloudTrunk):
            if _meta_flag(obj, "carrier_unreachable", "carrier_unavailable"):
                return _fail(self, obj, "Carrier is unreachable.")
            return _pass(self, obj, "Carrier reachability not reported as failed.")
        if isinstance(obj, ByocPremisesTrunk):
            if _meta_flag(obj, "carrier_unreachable", "carrier_unavailable"):
                return _fail(self, obj, "Carrier is unreachable.")
            return _pass(self, obj, "Carrier reachability not reported as failed.")
        endpoint = _require_type(obj, SipEndpoint)
        if _meta_flag(endpoint, "carrier_unreachable", "carrier_unavailable"):
            return _fail(self, endpoint, "Carrier is unreachable.")
        if not _has_text(endpoint.address):
            return _fail(self, endpoint, "Carrier endpoint address is missing.")
        return _pass(self, endpoint, "Carrier endpoint is configured.")


@dataclass(frozen=True)
class GenesysTlsCertificateExpiredRule(HealthRule):
    id: str = "genesys_tls_certificate_expired"
    title: str = "TLS certificate expired"
    description: str = "Expired TLS certificates break secure SIP trunks."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_SIP_ENDPOINT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        endpoint = _require_type(obj, SipEndpoint)
        status = (_meta_text(endpoint, "certificate_status", "tls_certificate_status") or "").lower()
        if _meta_flag(endpoint, "tls_certificate_expired") or status in {"expired", "invalid"}:
            return _fail(self, endpoint, "TLS certificate is expired.")
        return _pass(self, endpoint, "TLS certificate is valid or state unknown.")


@dataclass(frozen=True)
class GenesysTlsNegotiationFailureRule(HealthRule):
    id: str = "genesys_tls_negotiation_failure"
    title: str = "TLS negotiation failure"
    description: str = "TLS handshake failures prevent secure signaling."
    category: HealthCategory = HealthCategory.TLS
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_SIP_ENDPOINT,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        endpoint = _require_type(obj, SipEndpoint)
        status = (_meta_text(endpoint, "tls_status", "tls_negotiation_status") or "").lower()
        if _meta_flag(endpoint, "tls_negotiation_failure") or status in {
            "failed",
            "error",
            "negotiation_failed",
        }:
            return _fail(self, endpoint, "TLS negotiation failed.")
        transport = (endpoint.transport or "").lower()
        if transport == "tls" and _meta_flag(endpoint, "tls_failure"):
            return _fail(self, endpoint, "TLS negotiation failed.")
        return _pass(self, endpoint, "TLS negotiation not reported as failed.")


# ---------------------------------------------------------------------------
# Architect
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysArchitectPublishFailureRule(HealthRule):
    id: str = "genesys_architect_publish_failure"
    title: str = "Architect publish failure"
    description: str = "Architect flows must be published for production routing."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ARCHITECT_FLOW,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        flow = _require_type(obj, ArchitectFlow)
        publish = (flow.publish_state or "").lower()
        if _meta_flag(flow, "architect_publish_failure") or publish in {
            "failed",
            "unpublished",
            "error",
        }:
            return _fail(self, flow, "Architect flow publish failed.")
        return _pass(self, flow, "Architect flow publish state not reported as failed.")


@dataclass(frozen=True)
class GenesysDataActionFailureRule(HealthRule):
    id: str = "genesys_data_action_failure"
    title: str = "Data Action failure"
    description: str = "Architect Data Actions must be available for flow integrations."
    category: HealthCategory = HealthCategory.CONFIGURATION
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_DATA_ACTION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        action = _require_type(obj, DataAction)
        if _meta_flag(action, "data_action_failure") or _state_is_down(action.state):
            return _fail(self, action, "Data Action failed.")
        if not _has_text(action.endpoint_url):
            return _fail(self, action, "Data Action endpoint URL is missing.")
        return _pass(self, action, "Data Action is available.")


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysMediaServiceUnavailableRule(HealthRule):
    id: str = "genesys_media_service_unavailable"
    title: str = "Media service unavailable"
    description: str = "Genesys Cloud media services must be available for RTP."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "media_service_unavailable"):
            return _fail(self, organization, "Media service is unavailable.")
        media_state = (_meta_text(organization, "media_service_status", "media_status") or "").lower()
        if media_state in {"unavailable", "down", "failed"}:
            return _fail(self, organization, "Media service is unavailable.")
        return _pass(self, organization, "Media service not reported as unavailable.")


@dataclass(frozen=True)
class GenesysWebrtcFailureRule(HealthRule):
    id: str = "genesys_webrtc_failure"
    title: str = "WebRTC failure"
    description: str = "WebRTC services must be available for browser-based voice."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_GENESYS_ORGANIZATION,
        OBJECT_TYPE_GENESYS_AGENT,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, GenesysOrganization):
            if _meta_flag(obj, "webrtc_failure"):
                return _fail(self, obj, "WebRTC service failed.")
            webrtc_state = (_meta_text(obj, "webrtc_status") or "").lower()
            if webrtc_state in {"failed", "unavailable", "error"}:
                return _fail(self, obj, "WebRTC service failed.")
            return _pass(self, obj, "WebRTC not reported as failed at organization level.")
        agent = _require_type(obj, Agent)
        if _meta_flag(agent, "webrtc_failure"):
            return _fail(self, agent, "WebRTC failed for agent.")
        return _pass(self, agent, "WebRTC not reported as failed for agent.")


@dataclass(frozen=True)
class GenesysRecordingFailureRule(HealthRule):
    id: str = "genesys_recording_failure"
    title: str = "Recording failure"
    description: str = "Recording policies and sessions must be healthy."
    category: HealthCategory = HealthCategory.MEDIA
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (
        OBJECT_TYPE_GENESYS_RECORDING_POLICY,
        OBJECT_TYPE_GENESYS_RECORDING,
    )

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        if isinstance(obj, RecordingPolicy):
            if _meta_flag(obj, "recording_failure") or _state_is_down(obj.state):
                return _fail(self, obj, "Recording policy failed.")
            return _pass(self, obj, "Recording policy is healthy or state unknown.")
        recording = _require_type(obj, Recording)
        if _meta_flag(recording, "recording_failure") or _state_is_down(recording.state):
            return _fail(self, recording, "Recording session failed.")
        return _pass(self, recording, "Recording session is healthy or state unknown.")


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysOutboundCampaignFailureRule(HealthRule):
    id: str = "genesys_outbound_campaign_failure"
    title: str = "Outbound campaign failure"
    description: str = "Outbound campaigns must be running for dialer operations."
    category: HealthCategory = HealthCategory.ROUTING
    severity: HealthSeverity = HealthSeverity.HIGH
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_CAMPAIGN,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        campaign = _require_type(obj, Campaign)
        if _meta_flag(campaign, "outbound_campaign_failure") or _state_is_down(campaign.state):
            return _fail(self, campaign, "Outbound campaign failed.")
        return _pass(self, campaign, "Outbound campaign is healthy or state unknown.")


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenesysEdgeOfflineRule(HealthRule):
    id: str = "genesys_edge_offline"
    title: str = "Edge offline"
    description: str = "Genesys Cloud Edges must be online for premises connectivity."
    category: HealthCategory = HealthCategory.NETWORK
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_EDGE_DEVICE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        edge = _require_type(obj, EdgeDevice)
        if _meta_flag(edge, "edge_offline") or _state_matches(edge.state, _DOWN_STATES):
            return _fail(self, edge, "Edge is offline.")
        return _pass(self, edge, "Edge is online or state unknown.")


@dataclass(frozen=True)
class GenesysEdgeDegradedRule(HealthRule):
    id: str = "genesys_edge_degraded"
    title: str = "Edge degraded"
    description: str = "Degraded Edges may impact call quality and trunk availability."
    category: HealthCategory = HealthCategory.PERFORMANCE
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_EDGE_DEVICE,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        edge = _require_type(obj, EdgeDevice)
        state = (edge.state or "").lower()
        if _meta_flag(edge, "edge_degraded") or state in {"degraded", "warning", "impaired"}:
            return _fail(self, edge, "Edge is degraded.")
        return _pass(self, edge, "Edge is not reported as degraded.")


@dataclass(frozen=True)
class GenesysConversationServiceUnavailableRule(HealthRule):
    id: str = "genesys_conversation_service_unavailable"
    title: str = "Conversation service unavailable"
    description: str = "Conversation services must be available for contact handling."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.CRITICAL
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "conversation_service_unavailable"):
            return _fail(self, organization, "Conversation service is unavailable.")
        service_state = (
            _meta_text(organization, "conversation_service_status", "conversation_status") or ""
        ).lower()
        if service_state in {"unavailable", "down", "failed"}:
            return _fail(self, organization, "Conversation service is unavailable.")
        return _pass(self, organization, "Conversation service not reported as unavailable.")


@dataclass(frozen=True)
class GenesysAnalyticsServiceUnavailableRule(HealthRule):
    id: str = "genesys_analytics_service_unavailable"
    title: str = "Analytics service unavailable"
    description: str = "Analytics services must be available for reporting and WFM."
    category: HealthCategory = HealthCategory.GENERAL
    severity: HealthSeverity = HealthSeverity.MEDIUM
    supported_object_types: tuple[str, ...] = (OBJECT_TYPE_GENESYS_ORGANIZATION,)

    def evaluate(self, obj: VoiceObject, topology: VoiceTopology) -> HealthResult:
        organization = _require_type(obj, GenesysOrganization)
        if _meta_flag(organization, "analytics_unavailable", "analytics_service_unavailable"):
            return _fail(self, organization, "Analytics service is unavailable.")
        service_state = (_meta_text(organization, "analytics_status", "analytics_service_status") or "").lower()
        if service_state in {"unavailable", "down", "failed"}:
            return _fail(self, organization, "Analytics service is unavailable.")
        return _pass(self, organization, "Analytics service not reported as unavailable.")


GENESYS_HEALTH_RULES: tuple[HealthRule, ...] = (
    GenesysOauthFailureRule(),
    GenesysTokenExpiredRule(),
    GenesysOrganizationUnavailableRule(),
    GenesysAgentNotLoggedInRule(),
    GenesysAgentStuckInteractingRule(),
    GenesysPresenceSyncFailureRule(),
    GenesysUserRoutingDisabledRule(),
    GenesysQueueUnavailableRule(),
    GenesysQueueNoMembersRule(),
    GenesysQueueMemberUnavailableRule(),
    GenesysQueueOverloadedRule(),
    GenesysByocCloudUnavailableRule(),
    GenesysByocPremisesUnavailableRule(),
    GenesysSipOptionsFailureRule(),
    GenesysCarrierUnreachableRule(),
    GenesysTlsCertificateExpiredRule(),
    GenesysTlsNegotiationFailureRule(),
    GenesysArchitectPublishFailureRule(),
    GenesysDataActionFailureRule(),
    GenesysMediaServiceUnavailableRule(),
    GenesysWebrtcFailureRule(),
    GenesysRecordingFailureRule(),
    GenesysOutboundCampaignFailureRule(),
    GenesysEdgeOfflineRule(),
    GenesysEdgeDegradedRule(),
    GenesysConversationServiceUnavailableRule(),
    GenesysAnalyticsServiceUnavailableRule(),
)


def register_genesys_health_rules(registry) -> None:
    """Register Genesys Cloud health rules."""
    for rule in GENESYS_HEALTH_RULES:
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


def _meta_int(obj: VoiceObject, *keys: str) -> int | None:
    value = _meta_text(obj, *keys)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
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
