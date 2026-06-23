"""Canonical voice objects for Genesys Cloud CX (GVOM) investigations."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import (
    OBJECT_TYPE_GENESYS_ORGANIZATION,
    OBJECT_TYPE_GENESYS_REGION,
    OBJECT_TYPE_GENESYS_EDGE_DEVICE,
    OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,
    OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK,
    OBJECT_TYPE_GENESYS_SIP_ENDPOINT,
    OBJECT_TYPE_GENESYS_QUEUE,
    OBJECT_TYPE_GENESYS_QUEUE_MEMBER,
    OBJECT_TYPE_GENESYS_AGENT,
    OBJECT_TYPE_GENESYS_PRESENCE_DEFINITION,
    OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS,
    OBJECT_TYPE_GENESYS_FLOW,
    OBJECT_TYPE_GENESYS_ARCHITECT_FLOW,
    OBJECT_TYPE_GENESYS_DATA_ACTION,
    OBJECT_TYPE_GENESYS_CAMPAIGN,
    OBJECT_TYPE_GENESYS_WRAP_UP_CODE,
    OBJECT_TYPE_GENESYS_RECORDING_POLICY,
    OBJECT_TYPE_GENESYS_RECORDING,
    OBJECT_TYPE_GENESYS_DIVISION,
    OBJECT_TYPE_GENESYS_SKILL,
    VoiceObject,
    base_object_fields,
)
from shared.types import JsonDict


@dataclass(frozen=True)
class GenesysOrganization(VoiceObject):
    organization_id: str | None = None
    organization_name: str | None = None
    state: str | None = None
    domain: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        organization_id: str | None = None,
        organization_name: str | None = None,
        state: str | None = None,
        domain: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> GenesysOrganization:
        display = name or organization_id or "genesys-organization"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_ORGANIZATION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Cloud organization",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            organization_id=organization_id,
            organization_name=organization_name,
            state=state,
            domain=domain,
        )

@dataclass(frozen=True)
class GenesysRegion(VoiceObject):
    region_id: str | None = None
    region_name: str | None = None
    home_organization: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        region_id: str | None = None,
        region_name: str | None = None,
        home_organization: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> GenesysRegion:
        display = name or region_id or "genesys-region"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_REGION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Cloud region",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            region_id=region_id,
            region_name=region_name,
            home_organization=home_organization,
        )

@dataclass(frozen=True)
class EdgeDevice(VoiceObject):
    edge_id: str | None = None
    edge_name: str | None = None
    state: str | None = None
    organization_id: str | None = None
    software_version: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        edge_id: str | None = None,
        edge_name: str | None = None,
        state: str | None = None,
        organization_id: str | None = None,
        software_version: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> EdgeDevice:
        display = name or edge_id or "genesys-edge_device"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_EDGE_DEVICE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Cloud Edge device",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            edge_id=edge_id,
            edge_name=edge_name,
            state=state,
            organization_id=organization_id,
            software_version=software_version,
        )

@dataclass(frozen=True)
class ByocCloudTrunk(VoiceObject):
    trunk_id: str | None = None
    trunk_name: str | None = None
    state: str | None = None
    sip_options_status: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        trunk_id: str | None = None,
        trunk_name: str | None = None,
        state: str | None = None,
        sip_options_status: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ByocCloudTrunk:
        display = name or trunk_id or "genesys-byoc_cloud_trunk"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_BYOC_CLOUD_TRUNK,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys BYOC Cloud trunk",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            trunk_id=trunk_id,
            trunk_name=trunk_name,
            state=state,
            sip_options_status=sip_options_status,
        )

@dataclass(frozen=True)
class ByocPremisesTrunk(VoiceObject):
    trunk_id: str | None = None
    trunk_name: str | None = None
    state: str | None = None
    edge_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        trunk_id: str | None = None,
        trunk_name: str | None = None,
        state: str | None = None,
        edge_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ByocPremisesTrunk:
        display = name or trunk_id or "genesys-byoc_premises_trunk"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_BYOC_PREMISES_TRUNK,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys BYOC Premises trunk",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            trunk_id=trunk_id,
            trunk_name=trunk_name,
            state=state,
            edge_id=edge_id,
        )

@dataclass(frozen=True)
class SipEndpoint(VoiceObject):
    endpoint_id: str | None = None
    endpoint_name: str | None = None
    address: str | None = None
    transport: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        endpoint_id: str | None = None,
        endpoint_name: str | None = None,
        address: str | None = None,
        transport: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SipEndpoint:
        display = name or endpoint_id or "genesys-sip_endpoint"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_SIP_ENDPOINT,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys SIP endpoint",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            endpoint_id=endpoint_id,
            endpoint_name=endpoint_name,
            address=address,
            transport=transport,
        )

@dataclass(frozen=True)
class Queue(VoiceObject):
    queue_id: str | None = None
    queue_name: str | None = None
    state: str | None = None
    division_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        queue_id: str | None = None,
        queue_name: str | None = None,
        state: str | None = None,
        division_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Queue:
        display = name or queue_id or "genesys-queue"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_QUEUE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys ACD queue",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            queue_id=queue_id,
            queue_name=queue_name,
            state=state,
            division_id=division_id,
        )

@dataclass(frozen=True)
class QueueMember(VoiceObject):
    member_id: str | None = None
    queue_id: str | None = None
    user_id: str | None = None
    state: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        member_id: str | None = None,
        queue_id: str | None = None,
        user_id: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> QueueMember:
        display = name or member_id or "genesys-queue_member"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_QUEUE_MEMBER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys queue member",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            member_id=member_id,
            queue_id=queue_id,
            user_id=user_id,
            state=state,
        )

@dataclass(frozen=True)
class Agent(VoiceObject):
    agent_id: str | None = None
    user_id: str | None = None
    display_name: str | None = None
    state: str | None = None
    queue_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        display_name: str | None = None,
        state: str | None = None,
        queue_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Agent:
        display = name or agent_id or "genesys-agent"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_AGENT,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Cloud agent",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            agent_id=agent_id,
            user_id=user_id,
            display_name=display_name,
            state=state,
            queue_id=queue_id,
        )

@dataclass(frozen=True)
class PresenceDefinition(VoiceObject):
    presence_id: str | None = None
    presence_name: str | None = None
    system_presence: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        presence_id: str | None = None,
        presence_name: str | None = None,
        system_presence: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> PresenceDefinition:
        display = name or presence_id or "genesys-presence_definition"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_PRESENCE_DEFINITION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys presence definition",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            presence_id=presence_id,
            presence_name=presence_name,
            system_presence=system_presence,
        )

@dataclass(frozen=True)
class UserRoutingStatus(VoiceObject):
    user_id: str | None = None
    routing_status: str | None = None
    presence_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        user_id: str | None = None,
        routing_status: str | None = None,
        presence_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> UserRoutingStatus:
        display = name or user_id or "genesys-user_routing_status"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_USER_ROUTING_STATUS,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys user routing status",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            user_id=user_id,
            routing_status=routing_status,
            presence_id=presence_id,
        )

@dataclass(frozen=True)
class Flow(VoiceObject):
    flow_id: str | None = None
    flow_name: str | None = None
    state: str | None = None
    target_queue: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        flow_id: str | None = None,
        flow_name: str | None = None,
        state: str | None = None,
        target_queue: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Flow:
        display = name or flow_id or "genesys-flow"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_FLOW,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys inbound flow",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            flow_id=flow_id,
            flow_name=flow_name,
            state=state,
            target_queue=target_queue,
        )

@dataclass(frozen=True)
class ArchitectFlow(VoiceObject):
    flow_id: str | None = None
    flow_name: str | None = None
    publish_state: str | None = None
    data_action_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        flow_id: str | None = None,
        flow_name: str | None = None,
        publish_state: str | None = None,
        data_action_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ArchitectFlow:
        display = name or flow_id or "genesys-architect_flow"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_ARCHITECT_FLOW,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Architect flow",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            flow_id=flow_id,
            flow_name=flow_name,
            publish_state=publish_state,
            data_action_id=data_action_id,
        )

@dataclass(frozen=True)
class DataAction(VoiceObject):
    action_id: str | None = None
    action_name: str | None = None
    state: str | None = None
    endpoint_url: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        action_id: str | None = None,
        action_name: str | None = None,
        state: str | None = None,
        endpoint_url: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> DataAction:
        display = name or action_id or "genesys-data_action"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_DATA_ACTION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys Architect Data Action",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            action_id=action_id,
            action_name=action_name,
            state=state,
            endpoint_url=endpoint_url,
        )

@dataclass(frozen=True)
class Campaign(VoiceObject):
    campaign_id: str | None = None
    campaign_name: str | None = None
    state: str | None = None
    queue_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        campaign_id: str | None = None,
        campaign_name: str | None = None,
        state: str | None = None,
        queue_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Campaign:
        display = name or campaign_id or "genesys-campaign"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_CAMPAIGN,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys outbound campaign",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            state=state,
            queue_id=queue_id,
        )

@dataclass(frozen=True)
class WrapUpCode(VoiceObject):
    code_id: str | None = None
    code_name: str | None = None
    flow_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        code_id: str | None = None,
        code_name: str | None = None,
        flow_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> WrapUpCode:
        display = name or code_id or "genesys-wrap_up_code"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_WRAP_UP_CODE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys wrap-up code",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            code_id=code_id,
            code_name=code_name,
            flow_id=flow_id,
        )

@dataclass(frozen=True)
class RecordingPolicy(VoiceObject):
    policy_id: str | None = None
    policy_name: str | None = None
    state: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        policy_id: str | None = None,
        policy_name: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> RecordingPolicy:
        display = name or policy_id or "genesys-recording_policy"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_RECORDING_POLICY,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys recording policy",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            policy_id=policy_id,
            policy_name=policy_name,
            state=state,
        )

@dataclass(frozen=True)
class Recording(VoiceObject):
    recording_id: str | None = None
    policy_id: str | None = None
    state: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        recording_id: str | None = None,
        policy_id: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Recording:
        display = name or recording_id or "genesys-recording"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_RECORDING,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys call recording",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            recording_id=recording_id,
            policy_id=policy_id,
            state=state,
        )

@dataclass(frozen=True)
class Division(VoiceObject):
    division_id: str | None = None
    division_name: str | None = None
    state: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        division_id: str | None = None,
        division_name: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Division:
        display = name or division_id or "genesys-division"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_DIVISION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys division",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            division_id=division_id,
            division_name=division_name,
            state=state,
        )

@dataclass(frozen=True)
class Skill(VoiceObject):
    skill_id: str | None = None
    skill_name: str | None = None
    state: str | None = None
    division_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        vendor: str,
        platform: str,
        hostname: str,
        source_parser: str,
        source_command: str,
        source_evidence_id: str,
        skill_id: str | None = None,
        skill_name: str | None = None,
        state: str | None = None,
        division_id: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Skill:
        display = name or skill_id or "genesys-skill"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_GENESYS_SKILL,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Genesys routing skill",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            skill_id=skill_id,
            skill_name=skill_name,
            state=state,
            division_id=division_id,
        )
