#!/usr/bin/env python3
"""One-time generator for Genesys Cloud CX Professional Knowledge Pack v1."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
PRODUCT_DIR = "cloud"
VENDOR = "Genesys"
PRODUCT = "Cloud"
CREATED = "2026-06-22T12:00:00+00:00"

CATEGORY_MAP = {
    "AUTHENTICATION": "SECURITY",
    "OAUTH": "SECURITY",
    "TOKEN": "SECURITY",
    "ORGANIZATION": "MONITORING",
    "EDGE": "SIP",
    "TRUNK": "SIP",
    "CARRIER": "CALL_ROUTING",
    "SIP OPTIONS": "SIP",
    "TLS": "TLS",
    "QUEUE": "CALL_ROUTING",
    "AGENT": "COLLABORATION",
    "CALL FLOW": "ROUTING",
    "ARCHITECT": "GENERAL",
    "DATA ACTION": "GENERAL",
    "RECORDING": "MEDIA",
    "CONVERSATION": "VOICE",
    "ANALYTICS": "MONITORING",
    "WEBRTC": "MEDIA",
    "MEDIA": "MEDIA",
    "CAMPAIGN": "CALL_ROUTING",
    "PRESENCE": "COLLABORATION",
    "BYOC": "SIP",
}

INCIDENTS = (
    {
        "id": "000001",
        "slug": "authentication_failure",
        "title": "Authentication failure",
        "category": "AUTHENTICATION",
        "severity": "critical",
        "finding": "authentication_failure",
        "symptoms": [
            "Users cannot sign in to Genesys Cloud",
            "Admin console returns authentication errors",
            "API requests fail with 401 Unauthorized",
        ],
        "causes": [
            "Identity provider misconfiguration or outage",
            "Genesys Cloud authentication service degradation",
            "Incorrect SSO SAML or OIDC federation settings",
        ],
        "resolution": [
            "Verify identity provider availability and certificate validity",
            "Review Genesys Cloud status and authentication logs",
            "Validate SSO configuration against Genesys documentation",
        ],
        "rollback": ["Restore previous SSO and authentication configuration"],
        "health_rules": ["authentication_failure", "sso_authentication_failed"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
    {
        "id": "000002",
        "slug": "oauth_failure",
        "title": "OAuth failure",
        "category": "OAUTH",
        "severity": "critical",
        "finding": "oauth_failure",
        "symptoms": [
            "OAuth client authorization fails during API integration",
            "Token exchange returns invalid_grant or unauthorized_client",
            "Third-party integrations cannot authenticate to Genesys Cloud",
        ],
        "causes": [
            "OAuth client credentials rotated without application update",
            "Redirect URI mismatch on OAuth client registration",
            "Client lacks required OAuth scopes for API operations",
        ],
        "resolution": [
            "Verify OAuth client ID, secret, and redirect URI configuration",
            "Re-authorize application with required Genesys Cloud scopes",
            "Review OAuth client grant type and role assignments",
        ],
        "rollback": ["Restore previous OAuth client credentials and redirect URIs"],
        "health_rules": ["oauth_failure", "oauth_client_invalid"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
    {
        "id": "000003",
        "slug": "token_expired",
        "title": "Token expired",
        "category": "TOKEN",
        "severity": "high",
        "finding": "token_expired",
        "symptoms": [
            "API integrations fail with expired access token errors",
            "Agent workspace loses session unexpectedly",
            "Automated jobs fail after token refresh interval",
        ],
        "causes": [
            "Refresh token revoked or expired without renewal",
            "Clock skew between client and Genesys Cloud identity service",
            "Application not implementing token refresh correctly",
        ],
        "resolution": [
            "Re-authenticate OAuth client and obtain new tokens",
            "Verify system clock synchronization on integration hosts",
            "Implement and test automatic token refresh workflow",
        ],
        "rollback": ["Revoke new tokens and restore prior authorized client session"],
        "health_rules": ["token_expired", "access_token_invalid"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
    {
        "id": "000004",
        "slug": "organization_unavailable",
        "title": "Organization unavailable",
        "category": "ORGANIZATION",
        "severity": "critical",
        "finding": "organization_unavailable",
        "symptoms": [
            "Genesys Cloud organization fails to load in admin console",
            "All users in tenant cannot access applications",
            "Organization health dashboard shows degraded state",
        ],
        "causes": [
            "Genesys Cloud regional service outage",
            "Organization suspended or billing issue",
            "DNS or routing failure to organization endpoint",
        ],
        "resolution": [
            "Check Genesys Cloud status page and support advisories",
            "Verify organization billing and subscription status",
            "Engage Genesys support with organization ID and timestamps",
        ],
        "rollback": ["No configuration rollback during platform outage; document incident timeline"],
        "health_rules": ["organization_unavailable", "tenant_unreachable"],
        "related": ["RB-002", "VG-002", "REF-001"],
    },
    {
        "id": "000005",
        "slug": "edge_offline",
        "title": "Edge offline",
        "category": "EDGE",
        "severity": "critical",
        "finding": "edge_offline",
        "symptoms": [
            "Telephony Edge shows offline in Genesys Cloud admin",
            "PSTN calls fail for sites using affected Edge",
            "Edge heartbeat and registration alarms active",
        ],
        "causes": [
            "Edge appliance powered off or network unreachable",
            "Edge software crash or failed upgrade",
            "Firewall blocks Edge signaling to Genesys Cloud",
        ],
        "resolution": [
            "Verify Edge power, network connectivity, and DNS resolution",
            "Restart Edge services and review Edge diagnostic logs",
            "Confirm firewall permits required Edge cloud connectivity",
        ],
        "rollback": ["Restore previous Edge configuration from backup export"],
        "health_rules": ["edge_offline", "telephony_edge_unreachable"],
        "related": ["RB-002", "VG-002", "REF-003"],
    },
    {
        "id": "000006",
        "slug": "trunk_unavailable",
        "title": "Trunk unavailable",
        "category": "TRUNK",
        "severity": "high",
        "finding": "trunk_unavailable",
        "symptoms": [
            "Phone trunk shows unavailable in Genesys Cloud telephony admin",
            "Inbound and outbound PSTN calls fail on affected trunk",
            "Trunk health monitoring reports connection loss",
        ],
        "causes": [
            "SIP trunk registration or connectivity lost",
            "Carrier-side trunk maintenance or outage",
            "Incorrect trunk URI or authentication credentials",
        ],
        "resolution": [
            "Verify trunk registration status and SIP credentials",
            "Confirm carrier trunk health with provider NOC",
            "Review trunk base settings and failover configuration",
        ],
        "rollback": ["Restore previous trunk configuration from export"],
        "health_rules": ["trunk_unavailable", "sip_trunk_down"],
        "related": ["RB-003", "VG-003", "REF-003"],
    },
    {
        "id": "000007",
        "slug": "carrier_unavailable",
        "title": "Carrier unavailable",
        "category": "CARRIER",
        "severity": "high",
        "finding": "carrier_unavailable",
        "symptoms": [
            "All calls through carrier route fail with fast busy or reorder",
            "Carrier trunk group shows outage in monitoring",
            "Multiple destinations fail across same carrier path",
        ],
        "causes": [
            "Carrier network outage or maintenance window",
            "Carrier rate center or LATA routing failure",
            "Incorrect carrier trunk group assignment in Genesys Cloud",
        ],
        "resolution": [
            "Engage carrier NOC and confirm outage scope",
            "Fail over to alternate carrier trunk if configured",
            "Validate outbound route and carrier trunk group mapping",
        ],
        "rollback": ["Restore previous carrier trunk group routing assignment"],
        "health_rules": ["carrier_unavailable", "pstn_carrier_outage"],
        "related": ["RB-003", "VG-003", "REF-003"],
    },
    {
        "id": "000008",
        "slug": "sip_options_failed",
        "title": "SIP OPTIONS failed",
        "category": "SIP OPTIONS",
        "severity": "high",
        "finding": "sip_options_failure",
        "symptoms": [
            "SIP OPTIONS keepalive fails on Genesys Cloud trunk",
            "Trunk marked unavailable due to OPTIONS timeout",
            "Intermittent call setup failures on BYOC or Edge trunk",
        ],
        "causes": [
            "Peer does not respond to SIP OPTIONS",
            "Firewall drops OPTIONS in one direction",
            "OPTIONS timer mismatch between Genesys Cloud and peer SBC",
        ],
        "resolution": [
            "Enable SIP OPTIONS response on peer SBC or gateway",
            "Verify firewall permits OPTIONS bidirectionally",
            "Align OPTIONS interval with carrier or SBC requirements",
        ],
        "rollback": ["Restore previous trunk OPTIONS and keepalive settings"],
        "health_rules": ["sip_options_failure", "sip_options_timeout"],
        "related": ["RB-003", "VG-003", "REF-003"],
    },
    {
        "id": "000009",
        "slug": "tls_certificate_expired",
        "title": "TLS certificate expired",
        "category": "TLS",
        "severity": "critical",
        "finding": "tls_certificate_expired",
        "symptoms": [
            "TLS handshake failures on SIP or WebRTC connections",
            "Certificate expiry alarm in Edge or BYOC configuration",
            "Secure trunk or media path fails to establish",
        ],
        "causes": [
            "TLS certificate past notAfter date on Edge or SBC",
            "Incomplete certificate chain uploaded to telephony endpoint",
            "Automated certificate renewal not applied",
        ],
        "resolution": [
            "Renew TLS certificate and upload full chain",
            "Apply certificate to affected Edge, trunk, or WebRTC endpoint",
            "Validate peer accepts renewed certificate",
        ],
        "rollback": ["Restore previous valid certificate if renewal fails"],
        "health_rules": ["tls_certificate_expired"],
        "related": ["RB-004", "VG-004", "REF-003"],
    },
    {
        "id": "000010",
        "slug": "queue_unavailable",
        "title": "Queue unavailable",
        "category": "QUEUE",
        "severity": "high",
        "finding": "queue_unavailable",
        "symptoms": [
            "Inbound calls to queue receive fast busy or error treatment",
            "Queue shows zero available members in real-time views",
            "ACD routing fails to deliver calls to queue",
        ],
        "causes": [
            "Queue disabled or deleted in Genesys Cloud admin",
            "No routing path delivers calls to queue",
            "Queue membership configuration empty or invalid",
        ],
        "resolution": [
            "Verify queue exists and is enabled in admin console",
            "Review inbound call flow and queue assignment in Architect",
            "Confirm queue has valid member groups or agents assigned",
        ],
        "rollback": ["Restore previous queue and routing configuration"],
        "health_rules": ["queue_unavailable", "acd_queue_down"],
        "related": ["RB-005", "VG-005", "REF-004"],
    },
    {
        "id": "000011",
        "slug": "queue_member_unavailable",
        "title": "Queue member unavailable",
        "category": "QUEUE",
        "severity": "high",
        "finding": "queue_member_unavailable",
        "symptoms": [
            "Queue has members but none are routable",
            "Calls queue indefinitely without agent delivery",
            "Member status shows offline or not accepting interactions",
        ],
        "causes": [
            "All queue members logged out or in Do Not Disturb",
            "Queue member skill or group assignment mismatch",
            "Agent routing profile excludes queue members",
        ],
        "resolution": [
            "Verify agent login state and queue membership",
            "Review routing profile and queue member group assignments",
            "Confirm agents have required skills and licenses",
        ],
        "rollback": ["Restore previous queue membership and routing profile"],
        "health_rules": ["queue_member_unavailable", "no_available_agents"],
        "related": ["RB-005", "VG-005", "REF-004"],
    },
    {
        "id": "000012",
        "slug": "agent_not_logged_in",
        "title": "Agent not logged in",
        "category": "AGENT",
        "severity": "medium",
        "finding": "agent_not_logged_in",
        "symptoms": [
            "Agent cannot receive routed interactions",
            "Agent workspace shows logged out or disconnected",
            "Supervisor views show agent offline during scheduled shift",
        ],
        "causes": [
            "Agent did not complete login to Genesys Cloud workspace",
            "Authentication or license issue prevents agent session",
            "Station or phone association missing for agent",
        ],
        "resolution": [
            "Verify agent completes login to Genesys Cloud client",
            "Confirm agent license and role assignments",
            "Associate agent with valid station or WebRTC phone",
        ],
        "rollback": ["Restore previous agent station and profile assignment"],
        "health_rules": ["agent_not_logged_in", "agent_offline"],
        "related": ["RB-006", "VG-006", "REF-001"],
    },
    {
        "id": "000013",
        "slug": "agent_stuck_interacting",
        "title": "Agent stuck interacting",
        "category": "AGENT",
        "severity": "high",
        "finding": "agent_stuck_interacting",
        "symptoms": [
            "Agent remains in On Queue or Interacting state after call ends",
            "Agent cannot receive new interactions",
            "Supervisor cannot clear agent state from dashboard",
        ],
        "causes": [
            "Client disconnect without proper wrap-up completion",
            "Stuck interaction record in conversation service",
            "Routing or presence state machine desynchronization",
        ],
        "resolution": [
            "Supervisor clears stuck interaction from agent state",
            "Agent logs out and back in to reset client session",
            "Review client logs and conversation service for orphaned interaction",
        ],
        "rollback": ["Document manual state clear; no configuration change required"],
        "health_rules": ["agent_stuck_interacting", "stuck_interaction_state"],
        "related": ["RB-006", "VG-006", "REF-001"],
    },
    {
        "id": "000014",
        "slug": "call_flow_failure",
        "title": "Call flow failure",
        "category": "CALL FLOW",
        "severity": "high",
        "finding": "call_flow_failure",
        "symptoms": [
            "Inbound calls fail at IVR or routing decision point",
            "Call disconnects unexpectedly during Architect flow",
            "Error treatment plays instead of expected routing",
        ],
        "causes": [
            "Architect flow published with invalid or missing task",
            "Schedule or holiday group misconfiguration blocks routing",
            "Data table or participant data lookup failure in flow",
        ],
        "resolution": [
            "Review Architect flow execution trace for failure point",
            "Validate schedules, queues, and transfer targets in flow",
            "Republish flow after correcting invalid task configuration",
        ],
        "rollback": ["Republish previous Architect flow version from archive"],
        "health_rules": ["call_flow_failure", "architect_flow_error"],
        "related": ["RB-007", "VG-007", "REF-004"],
    },
    {
        "id": "000015",
        "slug": "architect_publish_issue",
        "title": "Architect publish issue",
        "category": "ARCHITECT",
        "severity": "high",
        "finding": "architect_publish_failure",
        "symptoms": [
            "Architect flow fails to publish to production",
            "Published flow version does not match editor configuration",
            "Inbound numbers still route to previous flow version",
        ],
        "causes": [
            "Validation errors in Architect flow before publish",
            "Missing dependency such as queue, schedule, or data table",
            "Concurrent publish conflict or permission issue",
        ],
        "resolution": [
            "Resolve Architect validation errors listed in publish report",
            "Verify all referenced objects exist and are accessible",
            "Republish flow with appropriate admin permissions",
        ],
        "rollback": ["Republish prior validated Architect flow version"],
        "health_rules": ["architect_publish_failure", "flow_validation_error"],
        "related": ["RB-007", "VG-007", "REF-004"],
    },
    {
        "id": "000016",
        "slug": "data_action_failure",
        "title": "Data Action failure",
        "category": "DATA ACTION",
        "severity": "high",
        "finding": "data_action_failure",
        "symptoms": [
            "Architect Data Action task fails during call flow",
            "External API integration returns error in flow trace",
            "Call routes to error handling after Data Action timeout",
        ],
        "causes": [
            "Data Action endpoint unreachable or returns error",
            "Authentication failure on external API called by Data Action",
            "Request or response mapping mismatch in Data Action configuration",
        ],
        "resolution": [
            "Test Data Action endpoint independently outside Architect",
            "Verify API credentials and OAuth for Data Action integration",
            "Review request mapping and timeout settings in Data Action",
        ],
        "rollback": ["Restore previous Data Action configuration and credentials"],
        "health_rules": ["data_action_failure", "integration_action_failed"],
        "related": ["RB-007", "VG-007", "REF-004"],
    },
    {
        "id": "000017",
        "slug": "recording_failure",
        "title": "Recording failure",
        "category": "RECORDING",
        "severity": "high",
        "finding": "recording_failure",
        "symptoms": [
            "Calls complete without expected recording artifact",
            "Recording policy applied but no recording file available",
            "Compliance alarm for missing call recordings",
        ],
        "causes": [
            "Recording policy not assigned to queue or flow",
            "Media recording service or storage quota exceeded",
            "Edge or cloud media path does not support recording",
        ],
        "resolution": [
            "Verify recording policy assignment on queue and Architect flow",
            "Check recording storage quota and retention settings",
            "Validate media path supports recording for interaction type",
        ],
        "rollback": ["Restore previous recording policy assignment"],
        "health_rules": ["recording_failure", "recording_policy_missing"],
        "related": ["RB-009", "VG-009", "REF-005"],
    },
    {
        "id": "000018",
        "slug": "conversation_service_unavailable",
        "title": "Conversation service unavailable",
        "category": "CONVERSATION",
        "severity": "critical",
        "finding": "conversation_service_unavailable",
        "symptoms": [
            "Active interactions cannot be controlled or transferred",
            "Agent and supervisor clients lose interaction state",
            "API conversation endpoints return service unavailable",
        ],
        "causes": [
            "Genesys Cloud conversation service regional degradation",
            "High API rate limiting or throttling on conversation endpoints",
            "Network path to conversation API blocked or unstable",
        ],
        "resolution": [
            "Check Genesys Cloud status for conversation service incidents",
            "Reduce concurrent API load if rate limiting detected",
            "Engage Genesys support with conversation IDs and timestamps",
        ],
        "rollback": ["No configuration rollback during platform service outage"],
        "health_rules": ["conversation_service_unavailable", "conversation_api_error"],
        "related": ["RB-009", "VG-009", "REF-001"],
    },
    {
        "id": "000019",
        "slug": "analytics_unavailable",
        "title": "Analytics unavailable",
        "category": "ANALYTICS",
        "severity": "medium",
        "finding": "analytics_unavailable",
        "symptoms": [
            "Historical reports and dashboards fail to load",
            "Real-time analytics widgets show no data",
            "Analytics API queries timeout or return errors",
        ],
        "causes": [
            "Genesys Cloud analytics pipeline delay or outage",
            "Insufficient analytics license or data retention scope",
            "Query exceeds analytics API limits or date range",
        ],
        "resolution": [
            "Verify Genesys Cloud analytics service status",
            "Confirm analytics licenses and data retention configuration",
            "Reduce query scope and retry after pipeline catch-up",
        ],
        "rollback": ["Restore previous analytics view and filter configuration"],
        "health_rules": ["analytics_unavailable", "analytics_pipeline_delay"],
        "related": ["RB-009", "VG-009", "REF-001"],
    },
    {
        "id": "000020",
        "slug": "webrtc_failure",
        "title": "WebRTC failure",
        "category": "WEBRTC",
        "severity": "high",
        "finding": "webrtc_failure",
        "symptoms": [
            "Agent WebRTC phone fails to register or place calls",
            "Browser shows media permission or ICE connection errors",
            "One-way or no audio on WebRTC interactions",
        ],
        "causes": [
            "Browser blocks microphone or lacks WebRTC permissions",
            "Corporate firewall blocks WebRTC UDP or TURN traffic",
            "STUN or TURN configuration incompatible with network",
        ],
        "resolution": [
            "Verify browser permissions and supported browser version",
            "Open required UDP ports and TURN relay paths in firewall",
            "Test WebRTC connectivity using Genesys network test tools",
        ],
        "rollback": ["Restore previous WebRTC phone and station assignment"],
        "health_rules": ["webrtc_failure", "webrtc_ice_failed"],
        "related": ["RB-008", "VG-008", "REF-005"],
    },
    {
        "id": "000021",
        "slug": "media_service_unavailable",
        "title": "Media service unavailable",
        "category": "MEDIA",
        "severity": "critical",
        "finding": "media_service_unavailable",
        "symptoms": [
            "Calls connect but have no audio path",
            "Media processing errors in interaction traces",
            "Conference or recording media tasks fail",
        ],
        "causes": [
            "Genesys Cloud media service regional degradation",
            "Edge media interface offline or misconfigured",
            "Codec or media region mismatch between endpoints",
        ],
        "resolution": [
            "Check Genesys Cloud media service status",
            "Verify Edge media interfaces and codec configuration",
            "Review media path selection in trunk and station settings",
        ],
        "rollback": ["Restore previous media and codec configuration"],
        "health_rules": ["media_service_unavailable", "media_path_failure"],
        "related": ["RB-008", "VG-008", "REF-005"],
    },
    {
        "id": "000022",
        "slug": "outbound_campaign_failure",
        "title": "Outbound campaign failure",
        "category": "CAMPAIGN",
        "severity": "high",
        "finding": "outbound_campaign_failure",
        "symptoms": [
            "Outbound campaign stops dialing or shows zero contacts processed",
            "Campaign contacts stuck in pending or error state",
            "Abandon or compliance metrics exceed thresholds",
        ],
        "causes": [
            "Campaign contact list exhausted or import failed",
            "Dialing mode or callable time window misconfiguration",
            "DNC or compliance rule blocks all outbound attempts",
        ],
        "resolution": [
            "Verify campaign contact list import and remaining records",
            "Review campaign schedule, dialing mode, and callable hours",
            "Validate DNC lists and compliance settings for campaign",
        ],
        "rollback": ["Pause campaign and restore previous contact list and rules"],
        "health_rules": ["outbound_campaign_failure", "campaign_dialing_stopped"],
        "related": ["RB-010", "VG-010", "REF-003"],
    },
    {
        "id": "000023",
        "slug": "presence_synchronization_issue",
        "title": "Presence synchronization issue",
        "category": "PRESENCE",
        "severity": "medium",
        "finding": "presence_synchronization_failure",
        "symptoms": [
            "Agent presence out of sync between client and supervisor views",
            "Routing delivers calls to agents marked unavailable",
            "Presence API shows stale state after status change",
        ],
        "causes": [
            "Client disconnect without presence state cleanup",
            "Multiple clients logged in with conflicting presence",
            "Presence subscription or notification delivery failure",
        ],
        "resolution": [
            "Agent logs out of all clients and re-establishes single session",
            "Supervisor clears stale presence from agent record",
            "Review presence integration and subscription configuration",
        ],
        "rollback": ["Restore previous presence routing and integration settings"],
        "health_rules": ["presence_synchronization_failure", "stale_presence_state"],
        "related": ["RB-006", "VG-006", "REF-001"],
    },
    {
        "id": "000024",
        "slug": "byoc_cloud_trunk_failure",
        "title": "BYOC Cloud trunk failure",
        "category": "BYOC",
        "severity": "critical",
        "finding": "byoc_cloud_trunk_failure",
        "symptoms": [
            "BYOC Cloud trunk shows unavailable in Genesys Cloud admin",
            "Inbound and outbound BYOC calls fail",
            "Carrier reports trunk deregistration from Genesys Cloud",
        ],
        "causes": [
            "BYOC Cloud trunk credentials or URI misconfiguration",
            "Carrier-side BYOC endpoint maintenance or outage",
            "TLS or SIP interoperability issue on BYOC trunk",
        ],
        "resolution": [
            "Verify BYOC Cloud trunk registration and credentials",
            "Confirm carrier BYOC endpoint status with provider",
            "Review TLS and SIP settings against carrier requirements",
        ],
        "rollback": ["Restore previous BYOC Cloud trunk configuration"],
        "health_rules": ["byoc_cloud_trunk_failure", "byoc_trunk_down"],
        "related": ["RB-010", "VG-010", "REF-003"],
    },
    {
        "id": "000025",
        "slug": "byoc_premises_edge_unavailable",
        "title": "BYOC Premises Edge unavailable",
        "category": "BYOC",
        "severity": "critical",
        "finding": "byoc_premises_edge_unavailable",
        "symptoms": [
            "BYOC Premises Edge offline in telephony admin",
            "On-premises PSTN path through Edge fails",
            "Edge pairing with Genesys Cloud lost",
        ],
        "causes": [
            "Premises Edge appliance offline or network isolated",
            "Edge pairing certificate or activation expired",
            "Firewall blocks Edge cloud management connectivity",
        ],
        "resolution": [
            "Verify Edge appliance power, network, and pairing status",
            "Reactivate or repair Edge pairing with Genesys Cloud",
            "Confirm firewall permits Edge management and signaling paths",
        ],
        "rollback": ["Restore previous BYOC Premises Edge configuration from backup"],
        "health_rules": ["byoc_premises_edge_unavailable", "edge_pairing_lost"],
        "related": ["RB-010", "VG-010", "REF-003"],
    },
)

RUNBOOKS = (
    ("RB-001", "validate_authentication_oauth", "Validate Authentication and OAuth", "RB-GENESYS-AUTH"),
    ("RB-002", "validate_organization_edge", "Validate Organization and Edge", "RB-GENESYS-EDGE"),
    ("RB-003", "validate_trunk_carrier", "Validate SIP Trunk and Carrier", "RB-GENESYS-TRUNK"),
    ("RB-004", "validate_tls_security", "Validate TLS and Security", "RB-GENESYS-TLS"),
    ("RB-005", "validate_queue_routing", "Validate Queue and Routing", "RB-GENESYS-QUEUE"),
    ("RB-006", "validate_agent_presence", "Validate Agent and Presence", "RB-GENESYS-AGENT"),
    ("RB-007", "validate_architect_call_flow", "Validate Architect and Call Flow", "RB-GENESYS-ARCHITECT"),
    ("RB-008", "validate_media_webrtc", "Validate Media and WebRTC", "RB-GENESYS-MEDIA"),
    ("RB-009", "validate_recording_conversation", "Validate Recording and Conversation", "RB-GENESYS-RECORDING"),
    ("RB-010", "validate_byoc_campaign", "Validate BYOC and Campaign", "RB-GENESYS-BYOC"),
)

VERIFICATIONS = (
    ("VG-001", "verify_authentication_oauth", "Verify authentication and OAuth", "VG-GENESYS-AUTH"),
    ("VG-002", "verify_organization_edge", "Verify organization and Edge health", "VG-GENESYS-EDGE"),
    ("VG-003", "verify_trunk_carrier", "Verify trunk and carrier connectivity", "VG-GENESYS-TRUNK"),
    ("VG-004", "verify_tls_security", "Verify TLS and certificate health", "VG-GENESYS-TLS"),
    ("VG-005", "verify_queue_routing", "Verify queue and routing", "VG-GENESYS-QUEUE"),
    ("VG-006", "verify_agent_presence", "Verify agent and presence state", "VG-GENESYS-AGENT"),
    ("VG-007", "verify_architect_call_flow", "Verify Architect and call flow", "VG-GENESYS-ARCHITECT"),
    ("VG-008", "verify_media_webrtc", "Verify media and WebRTC path", "VG-GENESYS-MEDIA"),
    ("VG-009", "verify_recording_conversation", "Verify recording and conversation service", "VG-GENESYS-RECORDING"),
    ("VG-010", "verify_byoc_campaign", "Verify BYOC and outbound campaign", "VG-GENESYS-BYOC"),
)

REFERENCES = (
    ("REF-001", "genesys_cloud_architecture", "Genesys Cloud Architecture"),
    ("REF-002", "oauth_authentication_reference", "OAuth and Authentication Reference"),
    ("REF-003", "edge_byoc_reference", "Edge and BYOC Reference"),
    ("REF-004", "architect_routing_reference", "Architect and Routing Reference"),
    ("REF-005", "media_webrtc_reference", "Media and WebRTC Reference"),
)


def asset_id(suffix: str) -> str:
    return f"VP-GENESYS-CLOUD-{suffix}"


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def incident_doc(item: dict) -> dict:
    related = [asset_id(related_id) for related_id in item["related"]]
    title = item["title"]
    if not title.lower().startswith("genesys"):
        title = f"Genesys Cloud {title}"
    return {
        "asset_id": asset_id(item["id"]),
        "title": title,
        "asset_type": "INCIDENT",
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": CATEGORY_MAP[item["category"]],
        "severity": item["severity"],
        "summary": f"{title} affecting Genesys Cloud CX operations.",
        "description": f"{title} affecting Genesys Cloud CX operations.",
        "symptoms": item["symptoms"],
        "required_evidence": [
            "Genesys Cloud admin configuration export",
            "Architect flow execution trace or interaction details",
            "Telephony trunk and Edge status screenshot",
        ],
        "expected_findings": [item["finding"], f"{item['slug']}_detected"],
        "expected_hypotheses": item["causes"],
        "known_causes": item["causes"],
        "known_resolution": item["resolution"],
        "recommended_actions": item["resolution"],
        "rollback_steps": item["rollback"],
        "verification_steps": [
            "Confirm expected findings in collected evidence",
            "Execute linked verification guide after remediation",
        ],
        "related_health_rules": item["health_rules"],
        "related_asset_ids": related,
        "tags": [
            "genesys-cloud",
            "professional-pack",
            "genesys",
            item["category"].lower().replace(" ", "-"),
        ],
        "references": [
            "Genesys Cloud CX Professional Pack v1",
            "Genesys Cloud Resource Center documentation",
        ],
        "confidence": 0.95,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def runbook_doc(suffix: str, slug: str, title: str, code: str, incidents: list[str], vgs: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "RUNBOOK",
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "high",
        "summary": f"{title} for Genesys Cloud CX.",
        "description": f"{title} for Genesys Cloud CX. Professional pack runbook {code}.",
        "symptoms": ["Service degradation requiring runbook remediation"],
        "expected_findings": ["runbook_remediation_required"],
        "expected_hypotheses": ["Known Genesys Cloud failure pattern matched"],
        "known_causes": ["Configuration or connectivity fault on Genesys Cloud"],
        "known_resolution": ["Execute runbook steps and validate with verification guide"],
        "recommended_actions": [
            f"Follow {code} remediation steps in order",
            "Document changes in change record",
            "Validate outcome with linked verification guide",
        ],
        "rollback_steps": [
            "Restore exported Genesys Cloud configuration",
            "Revert policy assignment to previous baseline",
        ],
        "verification_steps": ["Execute linked verification guide after remediation"],
        "related_asset_ids": [asset_id(item) for item in vgs + incidents],
        "tags": ["genesys-cloud", "runbook", "professional-pack", "genesys"],
        "references": ["Genesys Cloud CX Professional Pack v1", code],
        "confidence": 0.93,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def verification_doc(suffix: str, slug: str, title: str, code: str, rb: str, incidents: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "VERIFICATION_GUIDE",
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "medium",
        "summary": f"{title} for Genesys Cloud CX.",
        "description": f"{title} for Genesys Cloud CX. Professional pack guide {code}.",
        "symptoms": ["Post-remediation validation required"],
        "expected_findings": ["verification_passed"],
        "expected_hypotheses": ["Service restored to operational baseline"],
        "known_causes": ["Remediation not yet validated"],
        "known_resolution": ["Complete verification steps and attach evidence"],
        "required_evidence": [
            "Genesys Cloud status export after remediation",
            "Test interaction trace or SIP ladder diagram",
            "Configuration snapshot after change",
        ],
        "verification_steps": [
            f"Execute {code} validation checklist",
            "Compare results against expected operational baseline",
            "Attach evidence to investigation record",
        ],
        "recommended_actions": ["Compare results against expected operational baseline"],
        "related_asset_ids": [asset_id(rb), *[asset_id(item) for item in incidents]],
        "tags": ["genesys-cloud", "verification", "professional-pack", "genesys"],
        "references": ["Genesys Cloud CX Professional Pack v1", code],
        "confidence": 0.92,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def reference_doc(suffix: str, slug: str, title: str, incidents: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "REFERENCE",
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "low",
        "summary": f"{title} reference for Genesys Cloud CX engineering investigations.",
        "description": f"{title} for Genesys Cloud CX deployments and troubleshooting.",
        "symptoms": ["Engineering reference consultation required"],
        "expected_findings": ["reference_applicable"],
        "expected_hypotheses": ["Authoritative Genesys guidance applies"],
        "known_causes": ["Misconfiguration relative to Genesys Cloud best practice"],
        "known_resolution": ["Align design and remediation with Genesys guidance"],
        "recommended_actions": ["Consult this reference during investigation and remediation"],
        "verification_steps": ["Confirm document version matches deployed Genesys Cloud configuration"],
        "related_asset_ids": [asset_id(item) for item in incidents],
        "tags": ["genesys-cloud", "reference", "professional-pack", "genesys"],
        "references": [
            "https://help.mypurecloud.com/",
            "Genesys Cloud CX Professional Pack v1",
        ],
        "confidence": 0.99,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def main() -> None:
    rb_incidents = {rb[0]: [] for rb in RUNBOOKS}
    vg_incidents = {vg[0]: [] for vg in VERIFICATIONS}

    for item in INCIDENTS:
        for related in item["related"]:
            if related.startswith("RB-"):
                rb_incidents[related].append(item["id"])
            elif related.startswith("VG-"):
                vg_incidents[related].append(item["id"])

        path = KNOWLEDGE / "incidents" / "genesys" / PRODUCT_DIR / f"{item['slug']}.yaml"
        write_yaml(path, incident_doc(item))

    rb_vg_map = {f"RB-{index:03d}": [f"VG-{index:03d}"] for index in range(1, 11)}

    for suffix, slug, title, code in RUNBOOKS:
        path = KNOWLEDGE / "runbooks" / "genesys" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(
            path,
            runbook_doc(suffix, slug, title, code, rb_incidents[suffix][:3], rb_vg_map[suffix]),
        )

    vg_rb_map = {f"VG-{index:03d}": f"RB-{index:03d}" for index in range(1, 11)}

    for suffix, slug, title, code in VERIFICATIONS:
        path = KNOWLEDGE / "verification" / "genesys" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(
            path,
            verification_doc(suffix, slug, title, code, vg_rb_map[suffix], vg_incidents[suffix][:3]),
        )

    ref_map = {
        "REF-001": ["000004", "000012", "000013", "000018", "000019", "000023"],
        "REF-002": ["000001", "000002", "000003"],
        "REF-003": ["000005", "000006", "000007", "000008", "000009", "000022", "000024", "000025"],
        "REF-004": ["000010", "000011", "000014", "000015", "000016"],
        "REF-005": ["000017", "000020", "000021"],
    }

    for suffix, slug, title in REFERENCES:
        path = KNOWLEDGE / "references" / "genesys" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(path, reference_doc(suffix, slug, title, ref_map[suffix]))

    print(
        f"Generated {len(INCIDENTS)} incidents, {len(RUNBOOKS)} runbooks, "
        f"{len(VERIFICATIONS)} verification guides, {len(REFERENCES)} references"
    )


if __name__ == "__main__":
    main()
