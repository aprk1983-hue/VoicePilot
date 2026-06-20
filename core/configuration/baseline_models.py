"""Baseline and drift data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from configuration.diff_models import SnapshotDiff
from configuration.snapshot_models import ConfigurationSnapshot
from shared.types import JsonDict


class DriftStatus(str, Enum):
    """Drift classification relative to an approved baseline."""

    NO_DRIFT = "no_drift"
    LOW_DRIFT = "low_drift"
    MEDIUM_DRIFT = "medium_drift"
    HIGH_DRIFT = "high_drift"
    CRITICAL_DRIFT = "critical_drift"


@dataclass(frozen=True)
class Baseline:
    """Approved configuration baseline derived from a snapshot."""

    baseline_id: str
    snapshot_id: str
    hostname: str
    approved_by: str
    approved_at: datetime
    label: str
    description: str = ""
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class DriftReport:
    """Drift evaluation of a current snapshot against a baseline."""

    baseline: Baseline
    current_snapshot: ConfigurationSnapshot
    diff: SnapshotDiff
    drift_status: DriftStatus
    summary: str
    recommendations: tuple[str, ...] = ()
