"""Base voice object and relationship types for CVOM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from shared.constants import ID_PREFIX_VOICE_OBJECT
from shared.types import JsonDict

# Canonical object type identifiers (vendor-neutral).
OBJECT_TYPE_DEVICE = "device"
OBJECT_TYPE_INTERFACE = "interface"
OBJECT_TYPE_VOICE_SERVICE = "voice_service"
OBJECT_TYPE_SIP_UA = "sip_ua"
OBJECT_TYPE_DIAL_PEER = "dial_peer"
OBJECT_TYPE_CODEC_CLASS = "codec_class"
OBJECT_TYPE_SERVER_GROUP = "server_group"
OBJECT_TYPE_TRANSLATION_RULE = "translation_rule"
OBJECT_TYPE_TRANSLATION_PROFILE = "translation_profile"
OBJECT_TYPE_PROVIDER = "provider"
OBJECT_TYPE_CUCM_CLUSTER = "cucm_cluster"
OBJECT_TYPE_CUCM_NODE = "cucm_node"
OBJECT_TYPE_PHONE = "phone"
OBJECT_TYPE_SIP_TRUNK = "sip_trunk"
OBJECT_TYPE_GATEWAY = "gateway"
OBJECT_TYPE_ROUTE_PATTERN = "route_pattern"
OBJECT_TYPE_ROUTE_LIST = "route_list"
OBJECT_TYPE_ROUTE_GROUP = "route_group"
OBJECT_TYPE_CALLING_SEARCH_SPACE = "calling_search_space"
OBJECT_TYPE_PARTITION = "partition"
OBJECT_TYPE_DEVICE_POOL = "device_pool"
OBJECT_TYPE_REGION = "region"
OBJECT_TYPE_LOCATION = "location"
OBJECT_TYPE_MEDIA_RESOURCE_GROUP = "media_resource_group"
OBJECT_TYPE_MEDIA_RESOURCE_GROUP_LIST = "media_resource_group_list"
OBJECT_TYPE_MEDIA_TERMINATION_POINT = "media_termination_point"
OBJECT_TYPE_TRANSCODER = "transcoder"
OBJECT_TYPE_CONFERENCE_BRIDGE = "conference_bridge"
OBJECT_TYPE_TEAMS_USER = "teams_user"
OBJECT_TYPE_TEAMS_PHONE_NUMBER = "teams_phone_number"
OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY = "teams_voice_routing_policy"
OBJECT_TYPE_TEAMS_VOICE_ROUTE = "teams_voice_route"
OBJECT_TYPE_TEAMS_DIAL_PLAN = "teams_dial_plan"
OBJECT_TYPE_TEAMS_PSTN_GATEWAY = "teams_pstn_gateway"
OBJECT_TYPE_TEAMS_PSTN_USAGE = "teams_pstn_usage"
OBJECT_TYPE_TEAMS_CALL_QUEUE = "teams_call_queue"
OBJECT_TYPE_TEAMS_AUTO_ATTENDANT = "teams_auto_attendant"
OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT = "teams_resource_account"
OBJECT_TYPE_TEAMS_LIS_LOCATION = "teams_lis_location"
OBJECT_TYPE_AUDIOCODES_SBC_DEVICE = "audiocodes_sbc_device"
OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE = "audiocodes_sip_interface"
OBJECT_TYPE_AUDIOCODES_MEDIA_REALM = "audiocodes_media_realm"
OBJECT_TYPE_AUDIOCODES_PROXY_SET = "audiocodes_proxy_set"
OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS = "audiocodes_proxy_address"
OBJECT_TYPE_AUDIOCODES_IP_GROUP = "audiocodes_ip_group"
OBJECT_TYPE_AUDIOCODES_IP_PROFILE = "audiocodes_ip_profile"
OBJECT_TYPE_AUDIOCODES_ROUTING_RULE = "audiocodes_routing_rule"
OBJECT_TYPE_AUDIOCODES_MANIPULATION_SET = "audiocodes_manipulation_set"
OBJECT_TYPE_AUDIOCODES_MESSAGE_MANIPULATION = "audiocodes_message_manipulation"
OBJECT_TYPE_AUDIOCODES_TLS_CONTEXT = "audiocodes_tls_context"
OBJECT_TYPE_AUDIOCODES_CERTIFICATE = "audiocodes_certificate"
OBJECT_TYPE_AUDIOCODES_SRD = "audiocodes_srd"
OBJECT_TYPE_AUDIOCODES_ETHERNET_INTERFACE = "audiocodes_ethernet_interface"
OBJECT_TYPE_AUDIOCODES_HA_CLUSTER = "audiocodes_ha_cluster"
OBJECT_TYPE_AUDIOCODES_LICENSE = "audiocodes_license"
OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY = "audiocodes_sip_message_policy"
OBJECT_TYPE_AUDIOCODES_MEDIA_SECURITY_PROFILE = "audiocodes_media_security_profile"
OBJECT_TYPE_GENESYS_ORGANIZATION = "genesys_organization"
OBJECT_TYPE_GENESYS_REGION = "genesys_region"
OBJECT_TYPE_GENESYS_EDGE_DEVICE = "genesys_edge_device"
OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK = "genesys_byoc_cloud_trunk"
OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK = "genesys_byoc_premises_trunk"
OBJECT_TYPE_GENESYS_SIP_ENDPOINT = "genesys_sip_endpoint"
OBJECT_TYPE_GENESYS_QUEUE = "genesys_queue"
OBJECT_TYPE_GENESYS_QUEUE_MEMBER = "genesys_queue_member"
OBJECT_TYPE_GENESYS_AGENT = "genesys_agent"
OBJECT_TYPE_GENESYS_PRESENCE_DEFINITION = "genesys_presence_definition"
OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS = "genesys_user_routing_status"
OBJECT_TYPE_GENESYS_FLOW = "genesys_flow"
OBJECT_TYPE_GENESYS_ARCHITECT_FLOW = "genesys_architect_flow"
OBJECT_TYPE_GENESYS_DATA_ACTION = "genesys_data_action"
OBJECT_TYPE_GENESYS_CAMPAIGN = "genesys_campaign"
OBJECT_TYPE_GENESYS_WRAP_UP_CODE = "genesys_wrap_up_code"
OBJECT_TYPE_GENESYS_RECORDING_POLICY = "genesys_recording_policy"
OBJECT_TYPE_GENESYS_RECORDING = "genesys_recording"
OBJECT_TYPE_GENESYS_DIVISION = "genesys_division"
OBJECT_TYPE_GENESYS_SKILL = "genesys_skill"


def new_voice_object_id() -> str:
    """Generate a unique voice object identifier."""
    return f"{ID_PREFIX_VOICE_OBJECT}{uuid4().hex[:12]}"


@dataclass(frozen=True)
class VoiceObject:
    """Base immutable canonical voice object produced by parsers."""

    id: str
    object_type: str
    vendor: str
    platform: str
    hostname: str
    name: str
    description: str
    source_parser: str
    source_command: str
    source_evidence_id: str
    confidence: float
    metadata: JsonDict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError(f"confidence must be 0–100, got {self.confidence}")


@dataclass(frozen=True)
class VoiceRelationship:
    """Typed link between two canonical voice objects."""

    relationship_id: str
    relationship_type: str
    source_object_id: str
    target_object_id: str
    description: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        relationship_type: str,
        source_object_id: str,
        target_object_id: str,
        *,
        description: str = "",
        metadata: JsonDict | None = None,
    ) -> VoiceRelationship:
        return cls(
            relationship_id=f"VREL-{uuid4().hex[:12]}",
            relationship_type=relationship_type,
            source_object_id=source_object_id,
            target_object_id=target_object_id,
            description=description,
            metadata=dict(metadata or {}),
        )


def base_object_fields(
    *,
    object_type: str,
    vendor: str,
    platform: str,
    hostname: str,
    name: str,
    description: str,
    source_parser: str,
    source_command: str,
    source_evidence_id: str,
    confidence: float = 100.0,
    metadata: JsonDict | None = None,
    object_id: str | None = None,
) -> dict[str, Any]:
    """Build common VoiceObject field values for typed subclasses."""
    return {
        "id": object_id or new_voice_object_id(),
        "object_type": object_type,
        "vendor": vendor,
        "platform": platform,
        "hostname": hostname,
        "name": name,
        "description": description,
        "source_parser": source_parser,
        "source_command": source_command,
        "source_evidence_id": source_evidence_id,
        "confidence": confidence,
        "metadata": dict(metadata or {}),
    }
