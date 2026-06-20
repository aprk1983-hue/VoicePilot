"""Deterministic configuration diff engine."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from configuration.diff_models import (
    DiffChangeType,
    DiffRiskLevel,
    ObjectDiff,
    SnapshotDiff,
)
from configuration.snapshot_models import ConfigurationSnapshot
from model.dial_peer import DialPeer
from model.sip_ua import SipUA
from model.voice_graph import (
    OBJECT_TYPE_DIAL_PEER,
    OBJECT_TYPE_PROVIDER,
    OBJECT_TYPE_SIP_UA,
    OBJECT_TYPE_VOICE_SERVICE,
    VoiceObject,
)
from model.voice_service import VoiceService
from shared.types import JsonDict

PROVENANCE_FIELDS = frozenset(
    {
        "source_parser",
        "source_command",
        "source_evidence_id",
        "metadata",
        "confidence",
    }
)

_SEVERITY_ORDER = {
    DiffRiskLevel.NONE.value: 0,
    DiffRiskLevel.LOW.value: 1,
    DiffRiskLevel.MEDIUM.value: 2,
    DiffRiskLevel.HIGH.value: 3,
    DiffRiskLevel.CRITICAL.value: 4,
}


class DiffEngine:
    """Compare configuration snapshots and produce object-level diffs."""

    def compare(
        self,
        before_snapshot: ConfigurationSnapshot,
        after_snapshot: ConfigurationSnapshot,
    ) -> SnapshotDiff:
        """Compare two snapshots and return a deterministic diff."""
        before_index = {obj.id: obj for obj in before_snapshot.voice_objects}
        after_index = {obj.id: obj for obj in after_snapshot.voice_objects}

        added: list[ObjectDiff] = []
        removed: list[ObjectDiff] = []
        modified: list[ObjectDiff] = []
        unchanged_count = 0

        for object_id in sorted(before_index):
            before_object = before_index[object_id]
            after_object = after_index.get(object_id)
            if after_object is None:
                removed.append(_build_removed_diff(before_object))
                continue

            object_diff = self.compare_objects(before_object, after_object)
            if object_diff.change_type == DiffChangeType.UNCHANGED:
                unchanged_count += 1
            else:
                modified.append(object_diff)

        for object_id in sorted(after_index):
            if object_id not in before_index:
                added.append(_build_added_diff(after_index[object_id]))

        diff = SnapshotDiff(
            before_snapshot_id=before_snapshot.snapshot_id,
            after_snapshot_id=after_snapshot.snapshot_id,
            before_timestamp=before_snapshot.timestamp,
            after_timestamp=after_snapshot.timestamp,
            added=tuple(added),
            removed=tuple(removed),
            modified=tuple(modified),
            unchanged_count=unchanged_count,
        )
        return _finalize_snapshot_diff(diff)

    def compare_objects(
        self,
        before_object: VoiceObject,
        after_object: VoiceObject,
    ) -> ObjectDiff:
        """Compare two canonical voice objects, ignoring provenance-only fields."""
        before_payload = comparable_object_dict(before_object)
        after_payload = comparable_object_dict(after_object)
        before_hash = compute_object_hash(before_payload)
        after_hash = compute_object_hash(after_payload)

        if before_hash == after_hash:
            return ObjectDiff(
                object_id=before_object.id,
                object_type=before_object.object_type,
                object_name=before_object.name,
                change_type=DiffChangeType.UNCHANGED,
                before_hash=before_hash,
                after_hash=after_hash,
                before=before_payload,
                after=after_payload,
                severity=DiffRiskLevel.NONE.value,
                summary="No comparable field changes detected.",
            )

        changed_fields = tuple(
            sorted(
                field_name
                for field_name in sorted(set(before_payload) | set(after_payload))
                if before_payload.get(field_name) != after_payload.get(field_name)
            )
        )
        severity, summary = _assess_modified_risk(
            before_object,
            after_object,
            changed_fields,
            before_payload,
            after_payload,
        )
        return ObjectDiff(
            object_id=before_object.id,
            object_type=before_object.object_type,
            object_name=before_object.name,
            change_type=DiffChangeType.MODIFIED,
            before_hash=before_hash,
            after_hash=after_hash,
            changed_fields=changed_fields,
            before=before_payload,
            after=after_payload,
            severity=severity,
            summary=summary,
        )

    def summarize(self, diff: SnapshotDiff) -> str:
        """Return a concise human-readable diff summary."""
        return diff.summary


def comparable_object_dict(obj: VoiceObject) -> JsonDict:
    """Return comparable canonical fields for one voice object."""
    payload = asdict(obj)
    for field_name in PROVENANCE_FIELDS:
        payload.pop(field_name, None)
    return _normalize_mapping(payload)


def compute_object_hash(payload: JsonDict) -> str:
    """Return a deterministic SHA256 hash for comparable object content."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_added_diff(obj: VoiceObject) -> ObjectDiff:
    after_payload = comparable_object_dict(obj)
    severity = DiffRiskLevel.LOW.value
    summary = f"{obj.object_type} {obj.name} added"
    return ObjectDiff(
        object_id=obj.id,
        object_type=obj.object_type,
        object_name=obj.name,
        change_type=DiffChangeType.ADDED,
        after_hash=compute_object_hash(after_payload),
        after=after_payload,
        severity=severity,
        summary=summary,
    )


def _build_removed_diff(obj: VoiceObject) -> ObjectDiff:
    before_payload = comparable_object_dict(obj)
    severity, summary = _assess_removed_risk(obj)
    return ObjectDiff(
        object_id=obj.id,
        object_type=obj.object_type,
        object_name=obj.name,
        change_type=DiffChangeType.REMOVED,
        before_hash=compute_object_hash(before_payload),
        before=before_payload,
        severity=severity,
        summary=summary,
    )


def _assess_removed_risk(obj: VoiceObject) -> tuple[str, str]:
    if obj.object_type == OBJECT_TYPE_PROVIDER:
        return DiffRiskLevel.HIGH.value, f"Provider {obj.name} removed"
    if obj.object_type == OBJECT_TYPE_DIAL_PEER:
        return DiffRiskLevel.MEDIUM.value, f"DialPeer {obj.name} removed"
    return DiffRiskLevel.LOW.value, f"{obj.object_type} {obj.name} removed"


def _assess_modified_risk(
    before_object: VoiceObject,
    after_object: VoiceObject,
    changed_fields: tuple[str, ...],
    before_payload: JsonDict,
    after_payload: JsonDict,
) -> tuple[str, str]:
    if isinstance(before_object, SipUA) and isinstance(after_object, SipUA):
        if (
            "enabled" in changed_fields
            and before_object.enabled is True
            and after_object.enabled is False
        ):
            return (
                DiffRiskLevel.CRITICAL.value,
                "SipUA changed from enabled to disabled",
            )

    if isinstance(before_object, VoiceService) and isinstance(after_object, VoiceService):
        if "allow_connections" in changed_fields and before_object.allow_connections is True:
            if after_object.allow_connections is False or after_object.allow_connections is None:
                return (
                    DiffRiskLevel.HIGH.value,
                    "VoiceService allow_connections changed from enabled to disabled or missing",
                )

    if isinstance(before_object, DialPeer) and isinstance(after_object, DialPeer):
        if (
            "shutdown" in changed_fields
            and before_object.shutdown is False
            and after_object.shutdown is True
        ):
            return (
                DiffRiskLevel.HIGH.value,
                f"DialPeer {before_object.name} changed to shutdown",
            )
        if "destination_pattern" in changed_fields:
            return (
                DiffRiskLevel.MEDIUM.value,
                f"DialPeer {before_object.name} destination_pattern changed",
            )

    return (
        DiffRiskLevel.LOW.value,
        f"{before_object.object_type} {before_object.name} modified",
    )


def _finalize_snapshot_diff(diff: SnapshotDiff) -> SnapshotDiff:
    severities = [
        item.severity
        for item in (*diff.added, *diff.removed, *diff.modified)
        if item.severity
    ]
    risk_level = _max_severity(severities)
    summary = _build_snapshot_summary(diff, risk_level)
    return SnapshotDiff(
        before_snapshot_id=diff.before_snapshot_id,
        after_snapshot_id=diff.after_snapshot_id,
        before_timestamp=diff.before_timestamp,
        after_timestamp=diff.after_timestamp,
        added=diff.added,
        removed=diff.removed,
        modified=diff.modified,
        unchanged_count=diff.unchanged_count,
        summary=summary,
        risk_level=risk_level,
    )


def _build_snapshot_summary(diff: SnapshotDiff, risk_level: str) -> str:
    parts = [
        f"{len(diff.added)} added",
        f"{len(diff.removed)} removed",
        f"{len(diff.modified)} modified",
        f"{diff.unchanged_count} unchanged",
    ]
    return (
        f"Configuration diff between {diff.before_snapshot_id} and "
        f"{diff.after_snapshot_id}: {', '.join(parts)}. Risk level: {risk_level}."
    )


def _max_severity(severities: list[str]) -> str:
    if not severities:
        return DiffRiskLevel.NONE.value
    return max(severities, key=lambda item: _SEVERITY_ORDER.get(item.lower(), 0))


def _normalize_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_mapping(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize_mapping(item) for item in value]
    return value
