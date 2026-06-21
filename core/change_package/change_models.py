"""Frozen models for Engineering Change Packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from change_package.change_risk import ChangeRiskLevel


READ_ONLY_NOTICE = (
    "VoicePilot does not execute configuration changes. "
    "All changes must be reviewed, approved, and implemented by an authorized engineer."
)


@dataclass(frozen=True)
class VerificationStep:
    """Post-change verification step for engineer execution."""

    command: str
    expected_result: str
    purpose: str
    required: bool = True


@dataclass(frozen=True)
class ApprovalSection:
    """CAB / change advisory approval placeholder."""

    name: str
    required: bool
    placeholder: str


@dataclass(frozen=True)
class RecommendedChange:
    """Structured advisory change derived from investigation recommendations."""

    title: str
    reason: str
    current_state: str
    recommended_state: str
    config_example: str
    rollback_example: str
    verification: tuple[str, ...]
    risk_level: ChangeRiskLevel
    impacted_objects: tuple[str, ...]


@dataclass(frozen=True)
class EngineeringChangePackage:
    """Read-only engineering change advisory package for CAB review."""

    package_id: str
    case_id: str
    playbook_id: str | None
    generated_at: datetime
    title: str
    executive_summary: str
    root_cause: str | None
    confidence: float
    evidence_reviewed: tuple[str, ...]
    affected_components: tuple[str, ...]
    recommended_changes: tuple[RecommendedChange, ...]
    configuration_examples: tuple[str, ...]
    rollback_examples: tuple[str, ...]
    verification_steps: tuple[VerificationStep, ...]
    post_change_validation: tuple[str, ...]
    risk_level: ChangeRiskLevel
    risk_summary: str
    prerequisites: tuple[str, ...]
    assumptions: tuple[str, ...]
    related_knowledge_assets: tuple[str, ...]
    vendor_references: tuple[str, ...]
    approval_sections: tuple[ApprovalSection, ...]
    engineer_notes: tuple[str, ...]
    read_only_notice: str = READ_ONLY_NOTICE
