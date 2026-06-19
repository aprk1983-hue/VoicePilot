"""Immutable value objects for the VoicePilot domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from domain.enums import CostLevel, Severity
from shared.types import JsonDict


@dataclass(frozen=True)
class SymptomSummary:
    """Describes the reported incident symptom."""

    summary: str
    onset: datetime | None = None
    failure_mode: str | None = None
    metadata: JsonDict | None = None


@dataclass(frozen=True)
class AffectedScope:
    """Scope of users, sites, or destinations affected by the incident."""

    sites: tuple[str, ...] = ()
    call_direction: str | None = None
    destination_classes: tuple[str, ...] = ()
    metadata: JsonDict | None = None


@dataclass(frozen=True)
class PlatformRef:
    """Vendor-neutral platform reference."""

    vendor: str
    products: tuple[str, ...] = ()
    version_hints: JsonDict | None = None


@dataclass(frozen=True)
class EvidenceQuality:
    """Quality assessment for an evidence artifact."""

    completeness: float
    freshness: float
    reliability: float
    parseability: float
    overall: float


@dataclass(frozen=True)
class EvidenceSource:
    """Provenance for a collected evidence artifact."""

    origin: str
    collector: str
    device_id: str | None = None
    command: str | None = None


@dataclass(frozen=True)
class AlternativeConsidered:
    """A rejected alternative considered during a decision."""

    alternative: str
    rejection_reason: str


@dataclass(frozen=True)
class ConfidenceFactor:
    """Single factor contributing to a confidence score."""

    factor: str
    weight: float
    value: float
    contribution: float


@dataclass(frozen=True)
class CaseIntake:
    """Minimum data required to open a new investigation case."""

    title: str
    symptom: SymptomSummary
    severity: Severity
    business_impact: str
    affected_scope: AffectedScope
    platform: PlatformRef
    playbook_id: str | None = None
    assigned_engineer: str | None = None
    metadata: JsonDict | None = None
