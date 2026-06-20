"""Deterministic call path modeling over voice topology graphs."""

from __future__ import annotations

from model.dial_peer import DialPeer
from model.interface import Interface
from model.provider import Provider
from model.sip_ua import SipUA
from model.voice_graph import VoiceObject, VoiceRelationship
from model.voice_topology import VoiceTopology
from topology.call_path_models import CallPath, CallPathDirection, CallPathHop
from topology.dependency_engine import DependencyEngine
from topology.relationship_types import RelationshipType

_HEALTHY_STATUS = "healthy"
_UNKNOWN_STATUS = "unknown"
_UNHEALTHY_TOKENS = frozenset({"disabled", "down", "failed", "unregistered"})


class CallPathEngine:
    """Build deterministic call paths using topology dependency traversal."""

    def __init__(self, dependency_engine: DependencyEngine | None = None) -> None:
        self._dependency_engine = dependency_engine or DependencyEngine()

    def build_path(
        self,
        topology: VoiceTopology,
        source_object_id: str,
        destination_object_id: str,
        direction: CallPathDirection = CallPathDirection.UNKNOWN,
    ) -> CallPath:
        """Build a call path from source to destination when a dependency path exists."""
        object_index = {obj.id: obj for obj in topology.all_objects()}
        warnings: list[str] = []

        if source_object_id not in object_index:
            warnings.append(f"Source object not found: {source_object_id}")
            return _empty_call_path(
                source_object_id=source_object_id,
                destination_object_id=destination_object_id,
                direction=direction,
                warnings=tuple(warnings),
            )

        if destination_object_id not in object_index:
            warnings.append(f"Destination object not found: {destination_object_id}")
            return _empty_call_path(
                source_object_id=source_object_id,
                destination_object_id=destination_object_id,
                direction=direction,
                warnings=tuple(warnings),
            )

        if source_object_id == destination_object_id:
            source_object = object_index[source_object_id]
            hop = _object_to_hop(source_object, relationship_to_next=None)
            return CallPath(
                id=_call_path_id(source_object_id, destination_object_id),
                direction=direction,
                source_object_id=source_object_id,
                destination_object_id=destination_object_id,
                hops=(hop,),
                summary=_build_summary(source_object, source_object, hop_count=1),
                warnings=tuple(warnings),
            )

        relationships = self._dependency_engine.explain_dependency_path(
            topology,
            source_object_id,
            destination_object_id,
        )
        if not relationships:
            source_object = object_index[source_object_id]
            destination_object = object_index[destination_object_id]
            warnings.append(
                "No dependency path found from "
                f"{source_object.name} to {destination_object.name}."
            )
            return CallPath(
                id=_call_path_id(source_object_id, destination_object_id),
                direction=direction,
                source_object_id=source_object_id,
                destination_object_id=destination_object_id,
                hops=(),
                summary=(
                    f"No call path from {source_object.name} to {destination_object.name}."
                ),
                warnings=tuple(warnings),
            )

        hops = _relationships_to_hops(object_index, relationships)
        source_object = object_index[source_object_id]
        destination_object = object_index[destination_object_id]
        return CallPath(
            id=_call_path_id(source_object_id, destination_object_id),
            direction=direction,
            source_object_id=source_object_id,
            destination_object_id=destination_object_id,
            hops=hops,
            summary=_build_summary(source_object, destination_object, hop_count=len(hops)),
            warnings=tuple(warnings),
        )

    def build_outbound_paths(self, topology: VoiceTopology) -> tuple[CallPath, ...]:
        """Build outbound call paths for dial peers that route to providers."""
        paths: list[CallPath] = []
        for dial_peer in sorted(topology.dial_peers, key=lambda item: item.id):
            provider_ids = sorted(
                {
                    relationship.target_object_id
                    for relationship in topology.relationships
                    if (
                        relationship.source_object_id == dial_peer.id
                        and relationship.relationship_type == RelationshipType.ROUTES_TO.value
                    )
                }
            )
            for provider_id in provider_ids:
                paths.append(
                    self.build_path(
                        topology,
                        dial_peer.id,
                        provider_id,
                        direction=CallPathDirection.OUTBOUND,
                    )
                )

        return tuple(
            sorted(paths, key=lambda item: (item.source_object_id, item.destination_object_id))
        )

    def find_breakpoints(self, call_path: CallPath) -> tuple[CallPathHop, ...]:
        """Return hops with unhealthy status metadata; empty if no health data exists."""
        hops_with_health = tuple(hop for hop in call_path.hops if _hop_has_health_metadata(hop))
        if not hops_with_health:
            return ()

        return tuple(hop for hop in call_path.hops if _is_breakpoint_candidate(hop))


def _empty_call_path(
    *,
    source_object_id: str,
    destination_object_id: str,
    direction: CallPathDirection,
    warnings: tuple[str, ...],
) -> CallPath:
    return CallPath(
        id=_call_path_id(source_object_id, destination_object_id),
        direction=direction,
        source_object_id=source_object_id,
        destination_object_id=destination_object_id,
        hops=(),
        summary=f"No call path from {source_object_id} to {destination_object_id}.",
        warnings=warnings,
    )


def _call_path_id(source_object_id: str, destination_object_id: str) -> str:
    return f"CPATH-{source_object_id}-{destination_object_id}"


def _relationships_to_hops(
    object_index: dict[str, VoiceObject],
    relationships: tuple[VoiceRelationship, ...],
) -> tuple[CallPathHop, ...]:
    if not relationships:
        return ()

    hop_objects: list[VoiceObject] = [object_index[relationships[0].source_object_id]]
    hop_objects.extend(object_index[relationship.target_object_id] for relationship in relationships)

    hops: list[CallPathHop] = []
    for index, obj in enumerate(hop_objects):
        relationship_to_next = (
            relationships[index].relationship_type if index < len(relationships) else None
        )
        hops.append(_object_to_hop(obj, relationship_to_next=relationship_to_next))
    return tuple(hops)


def _object_to_hop(obj: VoiceObject, *, relationship_to_next: str | None) -> CallPathHop:
    health_status, findings, metadata, has_typed_health = _extract_health(obj)
    if not has_typed_health and not findings and not metadata:
        health_status = _UNKNOWN_STATUS

    return CallPathHop(
        object_id=obj.id,
        object_type=obj.object_type,
        label=obj.name,
        relationship_to_next=relationship_to_next,
        health_status=health_status,
        findings=findings,
        metadata=metadata,
    )


def _extract_health(
    obj: VoiceObject,
) -> tuple[str, tuple[str, ...], dict[str, object], bool]:
    findings: list[str] = []
    metadata: dict[str, object] = {}
    has_typed_health = False
    health_status = _UNKNOWN_STATUS

    if isinstance(obj, SipUA):
        if obj.enabled is not None:
            has_typed_health = True
            metadata["enabled"] = obj.enabled
            if obj.enabled is False:
                findings.append("disabled")
                health_status = "disabled"
            elif health_status == _UNKNOWN_STATUS:
                health_status = _HEALTHY_STATUS
        if obj.registered is not None:
            has_typed_health = True
            metadata["registered"] = obj.registered
            if obj.registered is False:
                findings.append("unregistered")
                health_status = "unregistered"
    elif isinstance(obj, DialPeer):
        if obj.status is not None:
            has_typed_health = True
            metadata["status"] = obj.status
            normalized = obj.status.strip().lower()
            if normalized in _UNHEALTHY_TOKENS:
                findings.append(normalized)
                health_status = normalized
            elif health_status == _UNKNOWN_STATUS:
                health_status = _HEALTHY_STATUS
        if obj.shutdown is True:
            has_typed_health = True
            metadata["shutdown"] = True
            findings.append("disabled")
            health_status = "disabled"
    elif isinstance(obj, Provider):
        if obj.status is not None:
            has_typed_health = True
            metadata["status"] = obj.status
            normalized = obj.status.strip().lower()
            if normalized in _UNHEALTHY_TOKENS:
                findings.append(normalized)
                health_status = normalized
            elif health_status == _UNKNOWN_STATUS:
                health_status = _HEALTHY_STATUS
    elif isinstance(obj, Interface):
        if obj.status is not None:
            has_typed_health = True
            metadata["status"] = obj.status
            normalized = obj.status.strip().lower()
            if normalized in _UNHEALTHY_TOKENS:
                findings.append(normalized)
                health_status = normalized
            elif health_status == _UNKNOWN_STATUS:
                health_status = _HEALTHY_STATUS

    for key, value in obj.metadata.items():
        if not isinstance(value, (str, bool, int, float)):
            continue
        normalized = str(value).strip().lower()
        if normalized in _UNHEALTHY_TOKENS or key.strip().lower() in _UNHEALTHY_TOKENS:
            has_typed_health = True
            metadata[key] = value
            if normalized in _UNHEALTHY_TOKENS and normalized not in findings:
                findings.append(normalized)
                health_status = normalized

    return health_status, tuple(sorted(set(findings))), metadata, has_typed_health


def _hop_has_health_metadata(hop: CallPathHop) -> bool:
    if hop.health_status != _UNKNOWN_STATUS:
        return True
    if hop.findings:
        return True
    return bool(hop.metadata)


def _is_breakpoint_candidate(hop: CallPathHop) -> bool:
    if hop.health_status.lower() in _UNHEALTHY_TOKENS:
        return True
    return any(finding.lower() in _UNHEALTHY_TOKENS for finding in hop.findings)


def _build_summary(
    source_object: VoiceObject,
    destination_object: VoiceObject,
    *,
    hop_count: int,
) -> str:
    hop_label = "hop" if hop_count == 1 else "hops"
    return (
        f"Call path from {source_object.name} to {destination_object.name} "
        f"via {hop_count} {hop_label}."
    )
