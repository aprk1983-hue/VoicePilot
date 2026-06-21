"""Engineering Asset Factory — production pipeline orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from asset_factory.asset_builder import AssetBuilder
from asset_factory.asset_quality import AssetQualityScore, AssetQualityScorer
from asset_factory.asset_relationship_builder import AssetRelationshipBuilder
from asset_factory.asset_statistics import AssetStatisticsGenerator, AssetStatisticsReport
from asset_factory.asset_validator import AssetValidator, BatchValidationReport
from engineering_assets.asset_models import EngineeringAsset, EngineeringRelationship


@dataclass(frozen=True)
class FactoryBuildResult:
    """Complete output from the asset production pipeline."""

    asset: EngineeringAsset
    validation: BatchValidationReport
    quality: AssetQualityScore
    relationships: tuple[EngineeringRelationship, ...]


class EngineeringAssetFactory:
    """Convert raw structured engineering content into validated production assets."""

    def __init__(
        self,
        *,
        builder: AssetBuilder | None = None,
        validator: AssetValidator | None = None,
        relationship_builder: AssetRelationshipBuilder | None = None,
        quality_scorer: AssetQualityScorer | None = None,
        statistics_generator: AssetStatisticsGenerator | None = None,
    ) -> None:
        self._builder = builder or AssetBuilder()
        self._validator = validator or AssetValidator()
        self._relationship_builder = relationship_builder or AssetRelationshipBuilder()
        self._quality_scorer = quality_scorer or AssetQualityScorer()
        self._statistics_generator = statistics_generator or AssetStatisticsGenerator(
            quality_scorer=self._quality_scorer
        )

    def build(self, data: dict[str, Any], *, source: str = "factory") -> FactoryBuildResult:
        """Run the full pipeline for one structured asset dictionary."""
        return self.build_batch((data,), source=source)[0]

    def build_batch(
        self,
        items: tuple[dict[str, Any], ...] | list[dict[str, Any]],
        *,
        source: str = "factory",
    ) -> tuple[FactoryBuildResult, ...]:
        """Run validation, normalization, relationship, quality, and statistics pipeline."""
        validation = self._validator.validate_batch(items)
        assets = self._builder.build_batch(items, source=source)
        asset_validation = self._validator.validate_assets(assets)
        relationships = self._relationship_builder.build_batch(assets)

        results: list[FactoryBuildResult] = []
        relationships_by_source: dict[str, tuple[EngineeringRelationship, ...]] = {}
        for relationship in relationships:
            relationships_by_source.setdefault(relationship.source_asset, ())
            existing = relationships_by_source[relationship.source_asset]
            relationships_by_source[relationship.source_asset] = existing + (relationship,)

        for asset in assets:
            quality = self._quality_scorer.score(asset)
            asset_relationships = relationships_by_source.get(asset.asset_id, ())
            results.append(
                FactoryBuildResult(
                    asset=asset,
                    validation=asset_validation,
                    quality=quality,
                    relationships=asset_relationships,
                )
            )

        return tuple(results)

    def validate_assets(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> BatchValidationReport:
        """Validate existing engineering assets."""
        return self._validator.validate_assets(assets)

    def asset_statistics(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
        *,
        relationships: tuple[EngineeringRelationship, ...] | list[EngineeringRelationship] | None = None,
    ) -> AssetStatisticsReport:
        """Generate statistics for an asset collection."""
        asset_tuple = tuple(assets)
        rels = relationships
        if rels is None:
            rels = self._relationship_builder.build_batch(asset_tuple)
        validation = self._validator.validate_assets(asset_tuple)
        return self._statistics_generator.generate(
            asset_tuple,
            relationships=tuple(rels),
            validation=validation,
        )

    def build_relationships(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> tuple[EngineeringRelationship, ...]:
        """Generate relationships for existing assets."""
        return self._relationship_builder.build_batch(assets)

    def score_quality(
        self,
        assets: tuple[EngineeringAsset, ...] | list[EngineeringAsset],
    ) -> tuple[AssetQualityScore, ...]:
        """Score quality for existing assets."""
        return self._quality_scorer.score_batch(assets)
