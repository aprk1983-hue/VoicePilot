"""Deterministic quality scoring for engineering assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_types import EngineeringAssetType


@dataclass(frozen=True)
class QualityCriterion:
    """One scored quality criterion."""

    name: str
    points: int
    max_points: int
    satisfied: bool


@dataclass(frozen=True)
class AssetQualityScore:
    """Quality score for one engineering asset."""

    asset_id: str
    score: int
    criteria: tuple[QualityCriterion, ...]


class AssetQualityScorer:
    """Generate deterministic 0–100 quality scores for engineering assets."""

    _CRITERIA: tuple[tuple[str, int], ...] = (
        ("Required metadata", 15),
        ("Relationships", 10),
        ("References", 10),
        ("Verification steps", 10),
        ("Runbook link", 10),
        ("Rollback", 5),
        ("Known symptoms", 10),
        ("Known findings", 10),
        ("Known causes", 10),
        ("Known resolution", 10),
    )

    def score(self, asset: EngineeringAsset) -> AssetQualityScore:
        """Score one engineering asset."""
        metadata = asset.metadata
        criteria = (
            self._criterion_required_metadata(asset),
            self._criterion_relationships(asset),
            self._criterion_references(asset),
            self._criterion_verification_steps(metadata),
            self._criterion_runbook_link(asset),
            self._criterion_rollback(metadata, asset.asset_type),
            self._criterion_known_symptoms(metadata),
            self._criterion_known_findings(metadata),
            self._criterion_known_causes(metadata),
            self._criterion_known_resolution(metadata),
        )
        total = sum(item.points for item in criteria)
        return AssetQualityScore(
            asset_id=asset.asset_id,
            score=min(total, 100),
            criteria=criteria,
        )

    def score_batch(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> tuple[AssetQualityScore, ...]:
        """Score multiple assets."""
        return tuple(self.score(asset) for asset in assets)

    def average_score(self, scores: tuple[AssetQualityScore, ...]) -> float:
        """Return average quality score."""
        if not scores:
            return 0.0
        return sum(item.score for item in scores) / len(scores)

    def _criterion_required_metadata(self, asset: EngineeringAsset) -> QualityCriterion:
        required = (
            asset.asset_id,
            asset.title,
            asset.summary,
            asset.vendor,
            asset.product,
            asset.version,
            asset.category,
            asset.status,
        )
        severity = asset.metadata.get("severity")
        satisfied = all(_non_empty(value) for value in required) and _non_empty(severity)
        return QualityCriterion("Required metadata", 15 if satisfied else 0, 15, satisfied)

    def _criterion_relationships(self, asset: EngineeringAsset) -> QualityCriterion:
        satisfied = bool(asset.related_asset_ids)
        return QualityCriterion("Relationships", 10 if satisfied else 0, 10, satisfied)

    def _criterion_references(self, asset: EngineeringAsset) -> QualityCriterion:
        satisfied = bool(asset.references)
        return QualityCriterion("References", 10 if satisfied else 0, 10, satisfied)

    def _criterion_verification_steps(self, metadata: dict[str, Any]) -> QualityCriterion:
        satisfied = _has_items(metadata.get("verification_steps"))
        return QualityCriterion("Verification steps", 10 if satisfied else 0, 10, satisfied)

    def _criterion_runbook_link(self, asset: EngineeringAsset) -> QualityCriterion:
        if asset.asset_type == EngineeringAssetType.RUNBOOK:
            satisfied = _has_items(asset.metadata.get("recommended_actions"))
        elif asset.asset_type == EngineeringAssetType.INCIDENT:
            satisfied = bool(asset.related_asset_ids)
        else:
            satisfied = bool(asset.related_asset_ids) or asset.asset_type in {
                EngineeringAssetType.REFERENCE,
                EngineeringAssetType.NOTE,
            }
        return QualityCriterion("Runbook link", 10 if satisfied else 0, 10, satisfied)

    def _criterion_rollback(self, metadata: dict[str, Any], asset_type: EngineeringAssetType) -> QualityCriterion:
        if asset_type != EngineeringAssetType.RUNBOOK:
            satisfied = True
            points = 5
        else:
            satisfied = _has_items(metadata.get("rollback_steps"))
            points = 5 if satisfied else 0
        return QualityCriterion("Rollback", points, 5, satisfied)

    def _criterion_known_symptoms(self, metadata: dict[str, Any]) -> QualityCriterion:
        satisfied = _has_items(metadata.get("symptoms"))
        return QualityCriterion("Known symptoms", 10 if satisfied else 0, 10, satisfied)

    def _criterion_known_findings(self, metadata: dict[str, Any]) -> QualityCriterion:
        satisfied = _has_items(metadata.get("expected_findings"))
        return QualityCriterion("Known findings", 10 if satisfied else 0, 10, satisfied)

    def _criterion_known_causes(self, metadata: dict[str, Any]) -> QualityCriterion:
        causes = metadata.get("known_causes") or metadata.get("expected_hypotheses")
        satisfied = _has_items(causes)
        return QualityCriterion("Known causes", 10 if satisfied else 0, 10, satisfied)

    def _criterion_known_resolution(self, metadata: dict[str, Any]) -> QualityCriterion:
        resolution = metadata.get("known_resolution") or metadata.get("recommended_actions")
        satisfied = _has_items(resolution)
        return QualityCriterion("Known resolution", 10 if satisfied else 0, 10, satisfied)


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _has_items(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)
