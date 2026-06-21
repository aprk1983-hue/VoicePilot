"""Canonical voice objects for Cisco CUCM investigations."""

from __future__ import annotations

from dataclasses import dataclass

from model.voice_graph import (
    OBJECT_TYPE_CALLING_SEARCH_SPACE,
    OBJECT_TYPE_CONFERENCE_BRIDGE,
    OBJECT_TYPE_CUCM_CLUSTER,
    OBJECT_TYPE_CUCM_NODE,
    OBJECT_TYPE_DEVICE_POOL,
    OBJECT_TYPE_GATEWAY,
    OBJECT_TYPE_LOCATION,
    OBJECT_TYPE_MEDIA_RESOURCE_GROUP,
    OBJECT_TYPE_MEDIA_RESOURCE_GROUP_LIST,
    OBJECT_TYPE_MEDIA_TERMINATION_POINT,
    OBJECT_TYPE_PARTITION,
    OBJECT_TYPE_PHONE,
    OBJECT_TYPE_REGION,
    OBJECT_TYPE_ROUTE_GROUP,
    OBJECT_TYPE_ROUTE_LIST,
    OBJECT_TYPE_ROUTE_PATTERN,
    OBJECT_TYPE_SIP_TRUNK,
    OBJECT_TYPE_TRANSCODER,
    VoiceObject,
    base_object_fields,
)
from shared.types import JsonDict


@dataclass(frozen=True)
class CUCMCluster(VoiceObject):
    publisher: str | None = None
    node_count: int | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, publisher: str | None = None, node_count: int | None = None, confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> CUCMCluster:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_CUCM_CLUSTER, vendor=vendor, platform=platform, hostname=hostname, name="cucm-cluster", description="CUCM cluster", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), publisher=publisher, node_count=node_count)


@dataclass(frozen=True)
class CUCMNode(VoiceObject):
    role: str | None = None
    service_state: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, role: str | None = None, service_state: str | None = None, name: str | None = None, confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> CUCMNode:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_CUCM_NODE, vendor=vendor, platform=platform, hostname=hostname, name=name or hostname, description="CUCM cluster node", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), role=role, service_state=service_state)


@dataclass(frozen=True)
class Phone(VoiceObject):
    mac_address: str | None = None
    registered: bool | None = None
    device_pool: str | None = None
    cm_node: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, mac_address: str | None = None, registered: bool | None = None, device_pool: str | None = None, cm_node: str | None = None, name: str = "phone", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Phone:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_PHONE, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM phone device", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), mac_address=mac_address, registered=registered, device_pool=device_pool, cm_node=cm_node)


@dataclass(frozen=True)
class SIPTrunk(VoiceObject):
    status: str | None = None
    destination: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, status: str | None = None, destination: str | None = None, name: str = "sip-trunk", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> SIPTrunk:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_SIP_TRUNK, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM SIP trunk", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), status=status, destination=destination)


@dataclass(frozen=True)
class Gateway(VoiceObject):
    status: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, status: str | None = None, name: str = "gateway", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Gateway:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_GATEWAY, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM gateway", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), status=status)


@dataclass(frozen=True)
class RoutePattern(VoiceObject):
    pattern: str | None = None
    partition: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, pattern: str | None = None, partition: str | None = None, name: str = "route-pattern", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> RoutePattern:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_ROUTE_PATTERN, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM route pattern", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), pattern=pattern, partition=partition)


@dataclass(frozen=True)
class RouteList(VoiceObject):
    route_group: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, route_group: str | None = None, name: str = "route-list", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> RouteList:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_ROUTE_LIST, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM route list", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), route_group=route_group)


@dataclass(frozen=True)
class RouteGroup(VoiceObject):
    member_count: int | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, member_count: int | None = None, name: str = "route-group", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> RouteGroup:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_ROUTE_GROUP, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM route group", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), member_count=member_count)


@dataclass(frozen=True)
class CallingSearchSpace(VoiceObject):
    partition_count: int | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, partition_count: int | None = None, name: str = "css", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> CallingSearchSpace:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_CALLING_SEARCH_SPACE, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM calling search space", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), partition_count=partition_count)


@dataclass(frozen=True)
class Partition(VoiceObject):
    accessible: bool | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, accessible: bool | None = None, name: str = "partition", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Partition:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_PARTITION, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM partition", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), accessible=accessible)


@dataclass(frozen=True)
class DevicePool(VoiceObject):
    region: str | None = None
    location: str | None = None
    mrgl: str | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, region: str | None = None, location: str | None = None, mrgl: str | None = None, name: str = "device-pool", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> DevicePool:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_DEVICE_POOL, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM device pool", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), region=region, location=location, mrgl=mrgl)


@dataclass(frozen=True)
class Region(VoiceObject):
    codec_list: tuple[str, ...] = ()

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, codec_list: tuple[str, ...] = (), name: str = "region", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Region:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_REGION, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM region", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), codec_list=codec_list)


@dataclass(frozen=True)
class Location(VoiceObject):
    bandwidth_kbps: int | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, bandwidth_kbps: int | None = None, name: str = "location", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Location:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_LOCATION, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM location", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), bandwidth_kbps=bandwidth_kbps)


@dataclass(frozen=True)
class MediaResourceGroup(VoiceObject):
    resource_type: str | None = None
    available: bool | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, resource_type: str | None = None, available: bool | None = None, name: str = "mrg", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> MediaResourceGroup:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_MEDIA_RESOURCE_GROUP, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM media resource group", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), resource_type=resource_type, available=available)


@dataclass(frozen=True)
class MediaResourceGroupList(VoiceObject):
    mrg_count: int | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, mrg_count: int | None = None, name: str = "mrgl", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> MediaResourceGroupList:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_MEDIA_RESOURCE_GROUP_LIST, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM MRGL", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), mrg_count=mrg_count)


@dataclass(frozen=True)
class MediaTerminationPoint(VoiceObject):
    available: bool | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, available: bool | None = None, name: str = "mtp", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> MediaTerminationPoint:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_MEDIA_TERMINATION_POINT, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM MTP", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), available=available)


@dataclass(frozen=True)
class Transcoder(VoiceObject):
    available: bool | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, available: bool | None = None, name: str = "transcoder", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> Transcoder:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_TRANSCODER, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM transcoder", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), available=available)


@dataclass(frozen=True)
class ConferenceBridge(VoiceObject):
    available: bool | None = None

    @classmethod
    def create(cls, *, vendor: str, platform: str, hostname: str, source_parser: str, source_command: str, source_evidence_id: str, available: bool | None = None, name: str = "conference-bridge", confidence: float = 100.0, metadata: JsonDict | None = None, object_id: str | None = None) -> ConferenceBridge:
        return cls(**base_object_fields(object_type=OBJECT_TYPE_CONFERENCE_BRIDGE, vendor=vendor, platform=platform, hostname=hostname, name=name, description="CUCM conference bridge", source_parser=source_parser, source_command=source_command, source_evidence_id=source_evidence_id, confidence=confidence, metadata=metadata, object_id=object_id), available=available)
