"""Canonical voice objects for Microsoft Teams Phone investigations."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import (
    OBJECT_TYPE_TEAMS_AUTO_ATTENDANT,
    OBJECT_TYPE_TEAMS_CALL_QUEUE,
    OBJECT_TYPE_TEAMS_DIAL_PLAN,
    OBJECT_TYPE_TEAMS_LIS_LOCATION,
    OBJECT_TYPE_TEAMS_PHONE_NUMBER,
    OBJECT_TYPE_TEAMS_PSTN_GATEWAY,
    OBJECT_TYPE_TEAMS_PSTN_USAGE,
    OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT,
    OBJECT_TYPE_TEAMS_USER,
    OBJECT_TYPE_TEAMS_VOICE_ROUTE,
    OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY,
    VoiceObject,
    base_object_fields,
)
from shared.types import JsonDict


@dataclass(frozen=True)
class TeamsUser(VoiceObject):
    user_principal_name: str | None = None
    enterprise_voice_enabled: bool | None = None
    line_uri: str | None = None
    voice_routing_policy: str | None = None
    dial_plan: str | None = None

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
        user_principal_name: str | None = None,
        enterprise_voice_enabled: bool | None = None,
        line_uri: str | None = None,
        voice_routing_policy: str | None = None,
        dial_plan: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsUser:
        display = name or user_principal_name or "teams-user"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_USER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Microsoft Teams Phone user",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            user_principal_name=user_principal_name,
            enterprise_voice_enabled=enterprise_voice_enabled,
            line_uri=line_uri,
            voice_routing_policy=voice_routing_policy,
            dial_plan=dial_plan,
        )


@dataclass(frozen=True)
class TeamsPhoneNumber(VoiceObject):
    telephone_number: str | None = None
    assigned_purpose: str | None = None
    assignment_status: str | None = None
    assigned_to: str | None = None

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
        telephone_number: str | None = None,
        assigned_purpose: str | None = None,
        assignment_status: str | None = None,
        assigned_to: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsPhoneNumber:
        display = name or telephone_number or "teams-phone-number"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_PHONE_NUMBER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Teams phone number assignment",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            telephone_number=telephone_number,
            assigned_purpose=assigned_purpose,
            assignment_status=assignment_status,
            assigned_to=assigned_to,
        )


@dataclass(frozen=True)
class TeamsVoiceRoutingPolicy(VoiceObject):
    route_type: str | None = None
    pstn_usages: tuple[str, ...] = ()

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
        route_type: str | None = None,
        pstn_usages: tuple[str, ...] | None = None,
        name: str = "voice-routing-policy",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsVoiceRoutingPolicy:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_VOICE_ROUTING_POLICY,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams voice routing policy",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            route_type=route_type,
            pstn_usages=pstn_usages or (),
        )


@dataclass(frozen=True)
class TeamsVoiceRoute(VoiceObject):
    number_pattern: str | None = None
    online_pstn_gateway_list: tuple[str, ...] = ()
    online_pstn_usages: tuple[str, ...] = ()
    priority: int | None = None

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
        number_pattern: str | None = None,
        online_pstn_gateway_list: tuple[str, ...] | None = None,
        online_pstn_usages: tuple[str, ...] | None = None,
        priority: int | None = None,
        name: str = "voice-route",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsVoiceRoute:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_VOICE_ROUTE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams online voice route",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            number_pattern=number_pattern,
            online_pstn_gateway_list=online_pstn_gateway_list or (),
            online_pstn_usages=online_pstn_usages or (),
            priority=priority,
        )


@dataclass(frozen=True)
class TeamsDialPlan(VoiceObject):
    normalization_rules_count: int | None = None
    external_access_prefix: str | None = None

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
        normalization_rules_count: int | None = None,
        external_access_prefix: str | None = None,
        name: str = "dial-plan",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsDialPlan:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_DIAL_PLAN,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams tenant dial plan",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            normalization_rules_count=normalization_rules_count,
            external_access_prefix=external_access_prefix,
        )


@dataclass(frozen=True)
class TeamsPstnGateway(VoiceObject):
    fqdn: str | None = None
    enabled: bool | None = None
    forward_call_history: bool | None = None

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
        fqdn: str | None = None,
        enabled: bool | None = None,
        forward_call_history: bool | None = None,
        name: str = "pstn-gateway",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsPstnGateway:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_PSTN_GATEWAY,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams Direct Routing PSTN gateway",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            fqdn=fqdn,
            enabled=enabled,
            forward_call_history=forward_call_history,
        )


@dataclass(frozen=True)
class TeamsPstnUsage(VoiceObject):
    usage: str | None = None

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
        usage: str | None = None,
        name: str = "pstn-usage",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsPstnUsage:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_PSTN_USAGE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams PSTN usage",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            usage=usage,
        )


@dataclass(frozen=True)
class TeamsCallQueue(VoiceObject):
    language_id: str | None = None
    distribution_lists: tuple[str, ...] = ()
    agents_count: int | None = None

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
        language_id: str | None = None,
        distribution_lists: tuple[str, ...] | None = None,
        agents_count: int | None = None,
        name: str = "call-queue",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsCallQueue:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_CALL_QUEUE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams call queue",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            language_id=language_id,
            distribution_lists=distribution_lists or (),
            agents_count=agents_count,
        )


@dataclass(frozen=True)
class TeamsAutoAttendant(VoiceObject):
    language_id: str | None = None
    time_zone_id: str | None = None
    operator: str | None = None

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
        language_id: str | None = None,
        time_zone_id: str | None = None,
        operator: str | None = None,
        name: str = "auto-attendant",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsAutoAttendant:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_AUTO_ATTENDANT,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams auto attendant",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            language_id=language_id,
            time_zone_id=time_zone_id,
            operator=operator,
        )


@dataclass(frozen=True)
class TeamsResourceAccount(VoiceObject):
    application_id: str | None = None
    application_type: str | None = None
    phone_number: str | None = None

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
        application_id: str | None = None,
        application_type: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsResourceAccount:
        display = name or application_id or "resource-account"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_RESOURCE_ACCOUNT,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="Teams resource account",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            application_id=application_id,
            application_type=application_type,
            phone_number=phone_number,
        )


@dataclass(frozen=True)
class TeamsLisLocation(VoiceObject):
    civic_address: str | None = None
    location: str | None = None
    e911_enabled: bool | None = None

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
        civic_address: str | None = None,
        location: str | None = None,
        e911_enabled: bool | None = None,
        name: str = "lis-location",
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TeamsLisLocation:
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_TEAMS_LIS_LOCATION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=name,
                description="Teams LIS emergency location",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            civic_address=civic_address,
            location=location,
            e911_enabled=e911_enabled,
        )
