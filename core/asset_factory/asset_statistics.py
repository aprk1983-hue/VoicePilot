"""Deterministic statistics for engineering asset collections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asset_factory.asset_quality import AssetQualityScore, AssetQualityScorer
from asset_factory.asset_validator import BatchValidationReport
from engineering_assets.asset_models import EngineeringAsset, EngineeringRelationship


@dataclass(frozen=True)
class AssetStatisticsReport:
    """Aggregate statistics for an engineering asset collection."""

    total_assets: int
    vendor_counts: tuple[tuple[str, int], ...]
    product_counts: tuple[tuple[str, int], ...]
    category_counts: tuple[tuple[str, int], ...]
    type_counts: tuple[tuple[str, int], ...]
    average_quality: float
    missing_references: int
    duplicate_ids: tuple[str, ...]
    duplicate_titles: tuple[str, ...]
    relationship_count: int
    quality_scores: tuple[AssetQualityScore, ...]


class AssetStatisticsGenerator:
    """Generate collection statistics for engineering assets."""

    def __init__(
        self,
        quality_scorer: AssetQualityScorer | None = None,
    ) -> None:
        self._quality_scorer = quality_scorer or AssetQualityScorer()

    def generate(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
        *,
        relationships: tuple[EngineeringRelationship, ...] | list[EngineeringRelationship] = (),
        validation: BatchValidationReport | None = None,
    ) -> AssetStatisticsReport:
        """Generate statistics for a collection of assets."""
        asset_tuple = tuple(assets)
        quality_scores = self._quality_scorer.score_batch(asset_tuple)

        vendor_counts = _count_field(asset.vendor or "(unspecified)" for asset in asset_tuple)
        product_counts = _count_field(asset.product or "(unspecified)" for asset in asset_tuple)
        category_counts = _count_field(asset.category.value for asset in asset_tuple)
        type_counts = _count_field(asset.asset_type.value for asset in asset_tuple)
        missing_references = sum(1 for asset in asset_tuple if not asset.references)

        duplicate_ids: tuple[str, ...] = ()
        duplicate_titles: tuple[str, ...] = ()
        if validation is not None:
            duplicate_ids = validation.duplicate_ids
            duplicate_titles = validation.duplicate_titles
        else:
            duplicate_ids = _find_duplicates(asset.asset_id for asset in asset_tuple)
            duplicate_titles = _find_duplicates(asset.title for asset in asset_tuple)

        return AssetStatisticsReport(
            total_assets=len(asset_tuple),
            vendor_counts=vendor_counts,
            product_counts=product_counts,
            category_counts=category_counts,
            type_counts=type_counts,
            average_quality=self._quality_scorer.average_score(quality_scores),
            missing_references=missing_references,
            duplicate_ids=duplicate_ids,
            duplicate_titles=duplicate_titles,
            relationship_count=len(tuple(relationships)),
            quality_scores=quality_scores,
        )


def _count_field(values: Any) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return tuple(sorted(counts.items()))


def _find_duplicates(values: Any) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(sorted(duplicates))
