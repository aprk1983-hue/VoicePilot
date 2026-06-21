"""Default templates and placeholders for engineering asset production."""

from __future__ import annotations

from typing import Any

from engineering_assets.asset_types import EngineeringAssetType

# Metadata fields promoted from top-level YAML into EngineeringAsset.metadata
METADATA_EXTENSION_FIELDS = (
    "severity",
    "symptoms",
    "required_evidence",
    "expected_findings",
    "expected_hypotheses",
    "related_health_rules",
    "related_discovery_rules",
    "related_knowledge_packs",
    "recommended_actions",
    "verification_steps",
    "rollback_steps",
    "known_causes",
    "known_resolution",
)

# Required top-level fields for factory-produced assets
REQUIRED_FACTORY_FIELDS = (
    "asset_id",
    "title",
    "asset_type",
    "category",
    "vendor",
    "product",
    "version",
    "summary",
    "status",
    "severity",
)

# Placeholder defaults applied during normalization
DEFAULT_PLACEHOLDERS: dict[str, Any] = {
    "description": "",
    "tags": [],
    "references": [],
    "related_asset_ids": [],
    "confidence": 1.0,
    "status": "ACTIVE",
    "version": "1.0",
    "severity": "medium",
    "symptoms": [],
    "required_evidence": [],
    "expected_findings": [],
    "expected_hypotheses": [],
    "recommended_actions": [],
    "verification_steps": [],
    "rollback_steps": [],
    "known_causes": [],
    "known_resolution": [],
}

# Asset-type-specific template overlays
ASSET_TYPE_TEMPLATES: dict[EngineeringAssetType, dict[str, Any]] = {
    EngineeringAssetType.INCIDENT: {
        "symptoms": ["Document observed symptoms"],
        "expected_findings": [],
        "expected_hypotheses": [],
        "verification_steps": ["Validate remediation using linked verification guide"],
    },
    EngineeringAssetType.RUNBOOK: {
        "recommended_actions": ["Follow runbook steps in order"],
        "verification_steps": ["Confirm service restored after remediation"],
        "rollback_steps": ["Document rollback procedure before change window"],
    },
    EngineeringAssetType.VERIFICATION_GUIDE: {
        "required_evidence": ["Collect verification command output"],
        "verification_steps": ["Compare output against expected baseline"],
    },
    EngineeringAssetType.REFERENCE: {
        "references": ["Add authoritative vendor or RFC reference URL"],
    },
    EngineeringAssetType.BEST_PRACTICE: {
        "recommended_actions": ["Apply best practice during design or remediation"],
    },
    EngineeringAssetType.BUG: {
        "known_causes": ["Document vendor bug root cause"],
        "known_resolution": ["Document vendor fix or workaround"],
    },
}

# Relationship chain order for automatic linking
RELATIONSHIP_CHAIN: tuple[EngineeringAssetType, ...] = (
    EngineeringAssetType.INCIDENT,
    EngineeringAssetType.RUNBOOK,
    EngineeringAssetType.VERIFICATION_GUIDE,
    EngineeringAssetType.REFERENCE,
    EngineeringAssetType.BEST_PRACTICE,
    EngineeringAssetType.BUG,
)

# Mapping from source type to relationship type for chain links
CHAIN_RELATIONSHIP_TYPES: dict[tuple[EngineeringAssetType, EngineeringAssetType], str] = {
    (EngineeringAssetType.INCIDENT, EngineeringAssetType.RUNBOOK): "IMPLEMENTS",
    (EngineeringAssetType.RUNBOOK, EngineeringAssetType.VERIFICATION_GUIDE): "VERIFIES",
    (EngineeringAssetType.VERIFICATION_GUIDE, EngineeringAssetType.REFERENCE): "REFERENCES",
    (EngineeringAssetType.REFERENCE, EngineeringAssetType.BEST_PRACTICE): "RELATED_TO",
    (EngineeringAssetType.BEST_PRACTICE, EngineeringAssetType.BUG): "KNOWN_ISSUE",
}
