"""Load engineering knowledge libraries from YAML asset directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engineering_assets import (
    EngineeringAsset,
    EngineeringAssetLoader,
    EngineeringAssetRegistry,
    EngineeringAssetSearch,
    EngineeringAssetType,
)
from engineering_knowledge.knowledge_exceptions import DuplicateKnowledgeRelationshipError
from engineering_knowledge.knowledge_models import (
    EngineeringKnowledge,
    KnowledgeRelationship,
    KnowledgeRelationshipType,
)
from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
from engineering_knowledge.knowledge_relationships import KnowledgeRelationshipRegistry


_LIBRARY_SUBDIRECTORIES = (
    "incidents",
    "runbooks",
    "verification",
    "references",
)


@dataclass(frozen=True)
class EngineeringKnowledgeLibrary:
    """Loaded engineering asset and knowledge library."""

    root: Path
    asset_registry: EngineeringAssetRegistry
    knowledge_registry: EngineeringKnowledgeRegistry
    relationship_registry: KnowledgeRelationshipRegistry


def default_knowledge_library_root() -> Path:
    """Return the repository knowledge library root."""
    return Path(__file__).resolve().parents[2] / "knowledge"


def iter_library_yaml_paths(root: Path) -> tuple[Path, ...]:
    """Return deterministic YAML paths for engineering knowledge libraries."""
    paths: list[Path] = []
    for subdirectory in _LIBRARY_SUBDIRECTORIES:
        directory = root / subdirectory
        if not directory.is_dir():
            continue
        paths.extend(sorted(path for path in directory.rglob("*.yaml") if path.is_file()))
    return tuple(paths)


def load_engineering_knowledge_library(
    root: Path | None = None,
    *,
    asset_registry: EngineeringAssetRegistry | None = None,
    knowledge_registry: EngineeringKnowledgeRegistry | None = None,
    relationship_registry: KnowledgeRelationshipRegistry | None = None,
) -> EngineeringKnowledgeLibrary:
    """Load YAML engineering assets and derive EKF knowledge entries."""
    library_root = root or default_knowledge_library_root()
    assets = asset_registry or EngineeringAssetRegistry()
    knowledge = knowledge_registry or EngineeringKnowledgeRegistry()
    relationships = relationship_registry or KnowledgeRelationshipRegistry()
    loader = EngineeringAssetLoader()

    for path in iter_library_yaml_paths(library_root):
        asset = loader.load_file(path)
        assets.register(asset)
        entry = build_engineering_knowledge_from_asset(asset)
        knowledge.register(entry)
        _register_asset_relationships(asset, relationships)

    return EngineeringKnowledgeLibrary(
        root=library_root,
        asset_registry=assets,
        knowledge_registry=knowledge,
        relationship_registry=relationships,
    )


def build_engineering_knowledge_from_asset(asset: EngineeringAsset) -> EngineeringKnowledge:
    """Derive an EKF knowledge entry from a loaded engineering asset."""
    metadata = dict(asset.metadata)
    match_signals = _string_tuple(metadata.get("expected_findings"))
    match_health_rule_ids = _string_tuple(metadata.get("related_health_rules"))
    asset_ids = (asset.asset_id, *asset.related_asset_ids)

    return EngineeringKnowledge(
        knowledge_id=asset.asset_id,
        title=asset.title,
        summary=asset.summary,
        asset_ids=asset_ids,
        tags=asset.tags,
        match_signals=match_signals,
        match_health_rule_ids=match_health_rule_ids,
        metadata={"asset_type": asset.asset_type.value, **metadata},
        source=asset.source,
        confidence=asset.confidence,
    )


def search_assets(
    library: EngineeringKnowledgeLibrary,
    query: str,
) -> tuple[EngineeringAsset, ...]:
    """Search loaded assets by text across common fields."""
    normalized = query.strip().lower()
    if not normalized:
        return library.asset_registry.list_assets()

    results: list[EngineeringAsset] = []
    for asset in library.asset_registry.list_assets():
        haystack = _asset_search_text(asset)
        if normalized in haystack:
            results.append(asset)
    return tuple(results)


def asset_stats(library: EngineeringKnowledgeLibrary) -> dict[str, Any]:
    """Return deterministic library statistics."""
    assets = library.asset_registry.list_assets()
    type_counts: dict[str, int] = {}
    vendor_counts: dict[str, int] = {}
    for asset in assets:
        type_counts[asset.asset_type.value] = type_counts.get(asset.asset_type.value, 0) + 1
        vendor = asset.vendor or "(unspecified)"
        vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
    return {
        "total_assets": len(assets),
        "total_knowledge_entries": len(library.knowledge_registry.list_knowledge()),
        "total_relationships": len(library.relationship_registry.list_relationships()),
        "type_counts": type_counts,
        "vendor_counts": vendor_counts,
    }


def format_asset_details(asset: EngineeringAsset) -> str:
    """Format one engineering asset for CLI display."""
    lines = [
        f"Asset ID:   {asset.asset_id}",
        f"Title:      {asset.title}",
        f"Type:       {asset.asset_type.value}",
        f"Vendor:     {asset.vendor}",
        f"Product:    {asset.product}",
        f"Category:   {asset.category.value}",
        f"Status:     {asset.status.value}",
        f"Summary:    {asset.summary}",
    ]
    if asset.description:
        lines.append(f"Description:{asset.description}")
    if asset.tags:
        lines.append(f"Tags:       {', '.join(asset.tags)}")
    if asset.related_asset_ids:
        lines.append(f"Related:    {', '.join(asset.related_asset_ids)}")
    if asset.references:
        lines.append("References:")
        lines.extend(f"  - {reference}" for reference in asset.references)

    metadata = asset.metadata
    for key in (
        "severity",
        "symptoms",
        "required_evidence",
        "expected_findings",
        "expected_hypotheses",
        "related_health_rules",
        "recommended_actions",
        "verification_steps",
    ):
        value = metadata.get(key)
        if value:
            lines.append(f"{key.replace('_', ' ').title()}:")
            if isinstance(value, list):
                lines.extend(f"  - {item}" for item in value)
            else:
                lines.append(f"  {value}")
    return "\n".join(lines)


def _register_asset_relationships(
    asset: EngineeringAsset,
    relationships: KnowledgeRelationshipRegistry,
) -> None:
    for related_asset_id in asset.related_asset_ids:
        relationship = KnowledgeRelationship(
            source_knowledge_id=asset.asset_id,
            target_knowledge_id=related_asset_id,
            relationship_type=KnowledgeRelationshipType.REFERENCES,
        )
        try:
            relationships.register(relationship)
        except DuplicateKnowledgeRelationshipError:
            continue


def _asset_search_text(asset: EngineeringAsset) -> str:
    parts = [
        asset.asset_id,
        asset.title,
        asset.summary,
        asset.description,
        asset.vendor,
        asset.product,
        " ".join(asset.tags),
    ]
    metadata = asset.metadata
    for key in ("symptoms", "expected_findings", "expected_hypotheses"):
        value = metadata.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value:
            parts.append(str(value))
    return " ".join(parts).lower()


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)
