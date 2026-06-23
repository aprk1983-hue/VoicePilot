"""Canonical voice objects for AudioCodes SBC (AVOM) investigations."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import (
    OBJECT_TYPE_AUDIOCODES_CERTIFICATE,
    OBJECT_TYPE_AUDIOCODES_ETHERNET_INTERFACE,
    OBJECT_TYPE_AUDIOCODES_HA_CLUSTER,
    OBJECT_TYPE_AUDIOCODES_IP_GROUP,
    OBJECT_TYPE_AUDIOCODES_IP_PROFILE,
    OBJECT_TYPE_AUDIOCODES_LICENSE,
    OBJECT_TYPE_AUDIOCODES_MANIPULATION_SET,
    OBJECT_TYPE_AUDIOCODES_MEDIA_REALM,
    OBJECT_TYPE_AUDIOCODES_MEDIA_SECURITY_PROFILE,
    OBJECT_TYPE_AUDIOCODES_MESSAGE_MANIPULATION,
    OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS,
    OBJECT_TYPE_AUDIOCODES_PROXY_SET,
    OBJECT_TYPE_AUDIOCODES_ROUTING_RULE,
    OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,
    OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,
    OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY,
    OBJECT_TYPE_AUDIOCODES_SRD,
    OBJECT_TYPE_AUDIOCODES_TLS_CONTEXT,
    VoiceObject,
    base_object_fields,
)
from shared.types import JsonDict


@dataclass(frozen=True)
class SBCDevice(VoiceObject):
    device_name: str | None = None
    software_version: str | None = None
    device_status: str | None = None

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
        device_name: str | None = None,
        software_version: str | None = None,
        device_status: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SBCDevice:
        display = name or device_name or hostname or "audiocodes-sbc"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_SBC_DEVICE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes SBC device",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            device_name=device_name,
            software_version=software_version,
            device_status=device_status,
        )


@dataclass(frozen=True)
class SIPInterface(VoiceObject):
    interface_name: str | None = None
    state: str | None = None
    transport: str | None = None
    port: int | None = None
    tls_context: str | None = None
    media_realm: str | None = None

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
        interface_name: str | None = None,
        state: str | None = None,
        transport: str | None = None,
        port: int | None = None,
        tls_context: str | None = None,
        media_realm: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SIPInterface:
        display = name or interface_name or "sip-interface"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_SIP_INTERFACE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes SIP Interface",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            interface_name=interface_name,
            state=state,
            transport=transport,
            port=port,
            tls_context=tls_context,
            media_realm=media_realm,
        )


@dataclass(frozen=True)
class MediaRealm(VoiceObject):
    realm_name: str | None = None
    state: str | None = None
    ip_address: str | None = None
    port_range: str | None = None

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
        realm_name: str | None = None,
        state: str | None = None,
        ip_address: str | None = None,
        port_range: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> MediaRealm:
        display = name or realm_name or "media-realm"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_MEDIA_REALM,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Media Realm",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            realm_name=realm_name,
            state=state,
            ip_address=ip_address,
            port_range=port_range,
        )


@dataclass(frozen=True)
class ProxySet(VoiceObject):
    proxy_set_name: str | None = None
    state: str | None = None
    enable_heartbeat: bool | None = None

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
        proxy_set_name: str | None = None,
        state: str | None = None,
        enable_heartbeat: bool | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ProxySet:
        display = name or proxy_set_name or "proxy-set"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_PROXY_SET,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Proxy Set",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            proxy_set_name=proxy_set_name,
            state=state,
            enable_heartbeat=enable_heartbeat,
        )


@dataclass(frozen=True)
class ProxyAddress(VoiceObject):
    proxy_set_name: str | None = None
    address: str | None = None
    transport: str | None = None
    port: int | None = None

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
        proxy_set_name: str | None = None,
        address: str | None = None,
        transport: str | None = None,
        port: int | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ProxyAddress:
        display = name or address or "proxy-address"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_PROXY_ADDRESS,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Proxy Address",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            proxy_set_name=proxy_set_name,
            address=address,
            transport=transport,
            port=port,
        )


@dataclass(frozen=True)
class IPGroup(VoiceObject):
    ip_group_name: str | None = None
    state: str | None = None
    proxy_set: str | None = None
    media_realm: str | None = None
    ip_profile: str | None = None

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
        ip_group_name: str | None = None,
        state: str | None = None,
        proxy_set: str | None = None,
        media_realm: str | None = None,
        ip_profile: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> IPGroup:
        display = name or ip_group_name or "ip-group"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_IP_GROUP,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes IP Group",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            ip_group_name=ip_group_name,
            state=state,
            proxy_set=proxy_set,
            media_realm=media_realm,
            ip_profile=ip_profile,
        )


@dataclass(frozen=True)
class IPProfile(VoiceObject):
    profile_name: str | None = None
    enable_srtp: bool | None = None

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
        profile_name: str | None = None,
        enable_srtp: bool | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> IPProfile:
        display = name or profile_name or "ip-profile"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_IP_PROFILE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes IP Profile",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            profile_name=profile_name,
            enable_srtp=enable_srtp,
        )


@dataclass(frozen=True)
class RoutingRule(VoiceObject):
    rule_name: str | None = None
    destination: str | None = None
    ip_group: str | None = None
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
        rule_name: str | None = None,
        destination: str | None = None,
        ip_group: str | None = None,
        priority: int | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> RoutingRule:
        display = name or rule_name or "routing-rule"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_ROUTING_RULE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes routing rule",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            rule_name=rule_name,
            destination=destination,
            ip_group=ip_group,
            priority=priority,
        )


@dataclass(frozen=True)
class ManipulationSet(VoiceObject):
    set_name: str | None = None
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
        set_name: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> ManipulationSet:
        display = name or set_name or "manipulation-set"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_MANIPULATION_SET,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Manipulation Set",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            set_name=set_name,
            state=state,
        )


@dataclass(frozen=True)
class MessageManipulation(VoiceObject):
    manipulation_name: str | None = None
    set_name: str | None = None
    action: str | None = None

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
        manipulation_name: str | None = None,
        set_name: str | None = None,
        action: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> MessageManipulation:
        display = name or manipulation_name or "message-manipulation"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_MESSAGE_MANIPULATION,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Message Manipulation",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            manipulation_name=manipulation_name,
            set_name=set_name,
            action=action,
        )


@dataclass(frozen=True)
class TLSContext(VoiceObject):
    context_name: str | None = None
    tls_version: str | None = None
    certificate_name: str | None = None

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
        context_name: str | None = None,
        tls_version: str | None = None,
        certificate_name: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> TLSContext:
        display = name or context_name or "tls-context"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_TLS_CONTEXT,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes TLS Context",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            context_name=context_name,
            tls_version=tls_version,
            certificate_name=certificate_name,
        )


@dataclass(frozen=True)
class Certificate(VoiceObject):
    certificate_name: str | None = None
    not_after: str | None = None
    status: str | None = None

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
        certificate_name: str | None = None,
        not_after: str | None = None,
        status: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> Certificate:
        display = name or certificate_name or "certificate"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_CERTIFICATE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes TLS certificate",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            certificate_name=certificate_name,
            not_after=not_after,
            status=status,
        )


@dataclass(frozen=True)
class SRD(VoiceObject):
    srd_name: str | None = None
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
        srd_name: str | None = None,
        state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SRD:
        display = name or srd_name or "srd"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_SRD,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Signaling Routing Domain",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            srd_name=srd_name,
            state=state,
        )


@dataclass(frozen=True)
class EthernetInterface(VoiceObject):
    interface_name: str | None = None
    state: str | None = None
    ip_address: str | None = None

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
        interface_name: str | None = None,
        state: str | None = None,
        ip_address: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> EthernetInterface:
        display = name or interface_name or "ethernet-interface"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_ETHERNET_INTERFACE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes Ethernet interface",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            interface_name=interface_name,
            state=state,
            ip_address=ip_address,
        )


@dataclass(frozen=True)
class HACluster(VoiceObject):
    cluster_state: str | None = None
    active_node: str | None = None
    standby_node: str | None = None
    sync_state: str | None = None

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
        cluster_state: str | None = None,
        active_node: str | None = None,
        standby_node: str | None = None,
        sync_state: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> HACluster:
        display = name or active_node or "ha-cluster"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_HA_CLUSTER,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes HA cluster",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            cluster_state=cluster_state,
            active_node=active_node,
            standby_node=standby_node,
            sync_state=sync_state,
        )


@dataclass(frozen=True)
class License(VoiceObject):
    license_type: str | None = None
    sessions_total: int | None = None
    sessions_used: int | None = None

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
        license_type: str | None = None,
        sessions_total: int | None = None,
        sessions_used: int | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> License:
        display = name or license_type or "license"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_LICENSE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes session license",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            license_type=license_type,
            sessions_total=sessions_total,
            sessions_used=sessions_used,
        )


@dataclass(frozen=True)
class SIPMessagePolicy(VoiceObject):
    policy_name: str | None = None
    options_enabled: bool | None = None

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
        policy_name: str | None = None,
        options_enabled: bool | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> SIPMessagePolicy:
        display = name or policy_name or "sip-message-policy"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_SIP_MESSAGE_POLICY,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes SIP message policy",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            policy_name=policy_name,
            options_enabled=options_enabled,
        )


@dataclass(frozen=True)
class MediaSecurityProfile(VoiceObject):
    profile_name: str | None = None
    srtp_mode: str | None = None

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
        profile_name: str | None = None,
        srtp_mode: str | None = None,
        name: str | None = None,
        confidence: float = 100.0,
        metadata: JsonDict | None = None,
        object_id: str | None = None,
    ) -> MediaSecurityProfile:
        display = name or profile_name or "media-security-profile"
        return cls(
            **base_object_fields(
                object_type=OBJECT_TYPE_AUDIOCODES_MEDIA_SECURITY_PROFILE,
                vendor=vendor,
                platform=platform,
                hostname=hostname,
                name=display,
                description="AudioCodes media security profile",
                source_parser=source_parser,
                source_command=source_command,
                source_evidence_id=source_evidence_id,
                confidence=confidence,
                metadata=metadata,
                object_id=object_id,
            ),
            profile_name=profile_name,
            srtp_mode=srtp_mode,
        )
