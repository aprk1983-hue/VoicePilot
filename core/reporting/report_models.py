"""Frozen models for the Enterprise Reporting Engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


READ_ONLY_NOTICE = (
    "VoicePilot is read-only. Reports summarize investigation results only. "
    "VoicePilot does not execute, push, or save configuration changes."
)


class ReportType(str, Enum):
    """Audience-specific enterprise report types."""

    ENGINEERING = "ENGINEERING"
    EXECUTIVE = "EXECUTIVE"
    CUSTOMER = "CUSTOMER"
    CAB = "CAB"
    OPERATIONS = "OPERATIONS"


@dataclass(frozen=True)
class BaseReport:
    """Common enterprise report envelope."""

    report_id: str
    case_id: str
    playbook_id: str | None
    report_type: ReportType
    generated_at: datetime
    title: str
    summary: str
    markdown: str


@dataclass(frozen=True)
class ExecutiveReport(BaseReport):
    """Executive audience report."""

    business_impact: str
    affected_services: tuple[str, ...]
    risk: str
    resolution: str
    confidence: float | None
    prevention: str
    next_actions: tuple[str, ...]


@dataclass(frozen=True)
class CustomerReport(BaseReport):
    """Customer-facing incident summary."""

    incident_summary: str
    business_language_impact: str
    resolution: str
    verification: str
    status: str


@dataclass(frozen=True)
class CABReport(BaseReport):
    """Change Advisory Board report."""

    change_summary: str
    reason: str
    affected_components: tuple[str, ...]
    risk: str
    rollback: tuple[str, ...]
    verification: tuple[str, ...]
    approvals: tuple[str, ...]
    implementation_window: str


@dataclass(frozen=True)
class EngineeringReport(BaseReport):
    """Engineering audience report wrapping existing incident markdown."""

    engineering_markdown: str


@dataclass(frozen=True)
class OperationsReport(BaseReport):
    """Operations and monitoring audience report."""

    health_score: int | None
    investigation_quality_score: int | None
    knowledge_matches: tuple[str, ...]
    open_findings: tuple[str, ...]
    recommendations: tuple[str, ...]
    future_monitoring: tuple[str, ...]
