"""Baseline drift evaluation engine."""

from __future__ import annotations

from configuration.baseline_models import Baseline, DriftReport, DriftStatus
from configuration.baseline_registry import BaselineRegistry
from configuration.diff_engine import DiffEngine
from configuration.diff_models import DiffRiskLevel, SnapshotDiff
from configuration.snapshot_exceptions import BaselineNotFoundError
from configuration.snapshot_models import ConfigurationSnapshot


class DriftEngine:
    """Compare current snapshots against approved baselines."""

    def __init__(
        self,
        diff_engine: DiffEngine | None = None,
        baseline_registry: BaselineRegistry | None = None,
    ) -> None:
        self._diff_engine = diff_engine or DiffEngine()
        self._baseline_registry = baseline_registry or BaselineRegistry()

    @property
    def baseline_registry(self) -> BaselineRegistry:
        """Return the baseline registry used for lookups."""
        return self._baseline_registry

    def compare_to_baseline(
        self,
        current_snapshot: ConfigurationSnapshot,
        baseline: Baseline,
        *,
        baseline_snapshot: ConfigurationSnapshot | None = None,
    ) -> DriftReport:
        """Compare a current snapshot to an approved baseline."""
        before_snapshot = baseline_snapshot or self._baseline_registry.get_snapshot(
            baseline.snapshot_id
        )
        if before_snapshot is None:
            raise BaselineNotFoundError(baseline.baseline_id)

        diff = self._diff_engine.compare(before_snapshot, current_snapshot)
        return _build_drift_report(baseline, current_snapshot, diff)

    def compare_to_latest_baseline(
        self,
        current_snapshot: ConfigurationSnapshot,
        hostname: str,
    ) -> DriftReport:
        """Compare a current snapshot to the latest baseline for a hostname."""
        baseline = self._baseline_registry.get_latest_baseline(hostname)
        if baseline is None:
            raise BaselineNotFoundError(hostname=hostname)
        return self.compare_to_baseline(current_snapshot, baseline)


def _build_drift_report(
    baseline: Baseline,
    current_snapshot: ConfigurationSnapshot,
    diff: SnapshotDiff,
) -> DriftReport:
    drift_status = _map_drift_status(diff)
    recommendations = _build_recommendations(drift_status)
    summary = (
        f"Drift status {drift_status.value} for {current_snapshot.hostname} "
        f"against baseline {baseline.baseline_id} ({baseline.label}). "
        f"{diff.summary}"
    )
    return DriftReport(
        baseline=baseline,
        current_snapshot=current_snapshot,
        diff=diff,
        drift_status=drift_status,
        summary=summary,
        recommendations=recommendations,
    )


def _map_drift_status(diff: SnapshotDiff) -> DriftStatus:
    has_changes = bool(diff.added or diff.removed or diff.modified)
    if not has_changes:
        return DriftStatus.NO_DRIFT

    risk = diff.risk_level.lower()
    if risk == DiffRiskLevel.CRITICAL.value:
        return DriftStatus.CRITICAL_DRIFT
    if risk == DiffRiskLevel.HIGH.value:
        return DriftStatus.HIGH_DRIFT
    if risk == DiffRiskLevel.MEDIUM.value:
        return DriftStatus.MEDIUM_DRIFT
    return DriftStatus.LOW_DRIFT


def _build_recommendations(drift_status: DriftStatus) -> tuple[str, ...]:
    mapping = {
        DriftStatus.NO_DRIFT: ("No action required.",),
        DriftStatus.LOW_DRIFT: ("Document change if expected.",),
        DriftStatus.MEDIUM_DRIFT: ("Review during next maintenance window.",),
        DriftStatus.HIGH_DRIFT: ("Validate changes against approved change record.",),
        DriftStatus.CRITICAL_DRIFT: ("Review immediately before production impact.",),
    }
    return mapping[drift_status]
