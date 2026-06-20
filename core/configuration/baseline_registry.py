"""In-memory approved baseline registry."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from configuration.baseline_models import Baseline
from configuration.snapshot_exceptions import DuplicateBaselineError
from configuration.snapshot_models import ConfigurationSnapshot
from shared.constants import ID_PREFIX_BASELINE
from shared.types import JsonDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaselineRegistry:
    """Register and lookup approved configuration baselines."""

    def __init__(self) -> None:
        self._baselines: dict[str, Baseline] = {}
        self._snapshots: dict[str, ConfigurationSnapshot] = {}

    def register_baseline(
        self,
        snapshot: ConfigurationSnapshot,
        approved_by: str,
        label: str,
        description: str = "",
        *,
        baseline_id: str | None = None,
        approved_at: datetime | None = None,
        metadata: JsonDict | None = None,
    ) -> Baseline:
        """Register an approved baseline for a snapshot."""
        resolved_id = baseline_id or _new_baseline_id()
        if resolved_id in self._baselines:
            raise DuplicateBaselineError(resolved_id)

        baseline = Baseline(
            baseline_id=resolved_id,
            snapshot_id=snapshot.snapshot_id,
            hostname=snapshot.hostname,
            approved_by=approved_by,
            approved_at=approved_at or _utc_now(),
            label=label,
            description=description,
            metadata=dict(metadata or {}),
        )
        self._baselines[resolved_id] = baseline
        self._snapshots[snapshot.snapshot_id] = snapshot
        return baseline

    def get_baseline(self, baseline_id: str) -> Baseline | None:
        """Return a baseline by identifier."""
        return self._baselines.get(baseline_id)

    def get_latest_baseline(self, hostname: str) -> Baseline | None:
        """Return the most recently approved baseline for a hostname."""
        normalized = hostname.strip().lower()
        matches = [
            baseline
            for baseline in self._baselines.values()
            if baseline.hostname.strip().lower() == normalized
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: (item.approved_at, item.baseline_id))

    def list_baselines(self, hostname: str | None = None) -> tuple[Baseline, ...]:
        """Return baselines ordered by approval time."""
        baselines = list(self._baselines.values())
        if hostname is not None:
            normalized = hostname.strip().lower()
            baselines = [
                baseline
                for baseline in baselines
                if baseline.hostname.strip().lower() == normalized
            ]
        return tuple(sorted(baselines, key=lambda item: (item.approved_at, item.baseline_id)))

    def get_snapshot(self, snapshot_id: str) -> ConfigurationSnapshot | None:
        """Return the snapshot captured when a baseline was registered."""
        return self._snapshots.get(snapshot_id)


def _new_baseline_id() -> str:
    return f"{ID_PREFIX_BASELINE}{uuid4().hex[:12]}"
