"""Domain entity models for VoicePilot investigations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from domain.enums import (
    DecisionType,
    EvidenceStatus,
    HypothesisStatus,
    InvestigationState,
    QuestionStatus,
    RecommendationStatus,
    Severity,
)
from domain.value_objects import (
    AffectedScope,
    AlternativeConsidered,
    ConfidenceFactor,
    EvidenceQuality,
    EvidenceSource,
    PlatformRef,
    SymptomSummary,
)
from shared.constants import (
    ID_PREFIX_CASE,
    ID_PREFIX_CONFIDENCE,
    ID_PREFIX_DECISION,
    ID_PREFIX_DEVICE,
    ID_PREFIX_EVIDENCE,
    ID_PREFIX_HYPOTHESIS,
    ID_PREFIX_QUESTION,
    ID_PREFIX_RECOMMENDATION,
    ID_PREFIX_STEP,
    ID_PREFIX_TIMELINE,
    ID_PREFIX_TOPOLOGY,
    ID_PREFIX_VERIFICATION,
)
from shared.types import JsonDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:12]}"


@dataclass
class Device:
    """Infrastructure component in a voice topology."""

    device_id: str
    case_id: str
    type: str
    role: str
    vendor: str
    hostname: str | None = None
    version: str | None = None
    zone: str | None = None
    extensions: JsonDict | None = None

    @classmethod
    def create(cls, case_id: str, type: str, role: str, vendor: str, **kwargs: Any) -> Device:
        return cls(device_id=_new_id(ID_PREFIX_DEVICE), case_id=case_id, type=type, role=role, vendor=vendor, **kwargs)


@dataclass
class Topology:
    """Voice path model for an investigation."""

    topology_id: str
    case_id: str
    pattern: str
    device_ids: list[str] = field(default_factory=list)
    relationships: list[JsonDict] = field(default_factory=list)
    completeness_score: float = 0.0
    updated_at: datetime = field(default_factory=_utc_now)


@dataclass
class Evidence:
    """Collected investigative artifact with provenance."""

    evidence_id: str
    case_id: str
    type: str
    title: str
    source: EvidenceSource
    collected_at: datetime
    quality: EvidenceQuality
    status: EvidenceStatus = EvidenceStatus.SUBMITTED
    source_artifact_id: str | None = None
    parser_finding_ids: list[str] = field(default_factory=list)
    supports_hypothesis_ids: list[str] = field(default_factory=list)
    contradicts_hypothesis_ids: list[str] = field(default_factory=list)


@dataclass
class Hypothesis:
    """Candidate or confirmed root cause explanation."""

    hypothesis_id: str
    case_id: str
    title: str
    status: HypothesisStatus = HypothesisStatus.CANDIDATE
    description: str | None = None
    category: str | None = None
    affected_device_ids: list[str] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    rank: int | None = None
    created_at: datetime = field(default_factory=_utc_now)


@dataclass
class Decision:
    """Recorded technical decision with audit metadata."""

    decision_id: str
    case_id: str
    sequence: int
    type: DecisionType
    decision: str
    reason: str
    evidence_ids: list[str]
    confidence: float
    timestamp: datetime
    actor: str
    alternatives_considered: list[AlternativeConsidered] = field(default_factory=list)
    hypothesis_id: str | None = None
    state_at_decision: InvestigationState | None = None
    engineer_acknowledged: bool = False


@dataclass
class Question:
    """Structured TAC-style investigative question."""

    question_id: str
    case_id: str
    text: str
    category: str
    phase: InvestigationState
    status: QuestionStatus = QuestionStatus.PENDING
    source: str = "playbook"
    target_fields: list[str] = field(default_factory=list)
    information_gain_score: float | None = None
    answer_structured: JsonDict | None = None
    asked_at: datetime | None = None
    answered_at: datetime | None = None


@dataclass
class Recommendation:
    """Proposed next investigative action."""

    recommendation_id: str
    case_id: str
    action_type: str
    description: str
    rationale: str
    cost_level: str
    information_gain: float
    priority_rank: int
    status: RecommendationStatus = RecommendationStatus.RECOMMENDED
    requires_engineer_approval: bool = False
    verification_steps: list[str] = field(default_factory=list)
    rollback_steps: list[str] = field(default_factory=list)
    target_device_id: str | None = None
    command: str | None = None


@dataclass
class Verification:
    """Post-resolution test record."""

    verification_id: str
    case_id: str
    step_name: str
    description: str
    expected_result: str
    actual_result: str | None = None
    passed: bool | None = None
    executed_at: datetime | None = None
    executed_by: str | None = None
    evidence_id: str | None = None


@dataclass
class TimelineEvent:
    """Chronological investigation event."""

    event_id: str
    case_id: str
    sequence: int
    timestamp: datetime
    event_type: str
    source_engine: str
    summary: str
    related_entity_ids: JsonDict = field(default_factory=dict)
    engineer_visible: bool = True


@dataclass
class InvestigationStep:
    """Planned or executed investigative action."""

    step_id: str
    case_id: str
    sequence: int
    action_type: str
    description: str
    cost_level: str
    status: str = "planned"
    target_device_id: str | None = None
    command: str | None = None
    recommendation_id: str | None = None
    evidence_id: str | None = None
    completed_at: datetime | None = None


@dataclass
class ConfidenceScore:
    """Point-in-time explainable confidence assessment."""

    confidence_score_id: str
    case_id: str
    score: float
    explanation: str
    factors: list[ConfidenceFactor] = field(default_factory=list)
    trend: str | None = None
    calculated_at: datetime = field(default_factory=_utc_now)
    calculated_by: str = "confidence-engine"


@dataclass
class Playbook:
    """Loaded DSL playbook definition."""

    playbook_id: str
    version: str
    title: str
    status: str
    raw_document: JsonDict
    vendor: str | None = None
    category: str | None = None


@dataclass
class Case:
    """Root aggregate for a VoicePilot investigation."""

    case_id: str
    title: str
    status: InvestigationState
    severity: Severity
    business_impact: str
    symptom: SymptomSummary
    affected_scope: AffectedScope
    platform: PlatformRef
    opened_at: datetime = field(default_factory=_utc_now)
    closed_at: datetime | None = None
    playbook_id: str | None = None
    playbook_version: str | None = None
    assigned_engineer: str | None = None
    strategy_id: str | None = None
    root_cause_id: str | None = None
    resolution_summary: str | None = None
    schema_version: str = "1.0"
    evidence: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    timeline_events: list[TimelineEvent] = field(default_factory=list)
    topology: Topology | None = None
    devices: list[Device] = field(default_factory=list)
    investigation_steps: list[InvestigationStep] = field(default_factory=list)
    confidence_scores: list[ConfidenceScore] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        title: str,
        symptom: SymptomSummary,
        severity: Severity,
        business_impact: str,
        affected_scope: AffectedScope,
        platform: PlatformRef,
        **kwargs: Any,
    ) -> Case:
        """Factory for a new case in ``NEW`` state."""
        return cls(
            case_id=_new_id(ID_PREFIX_CASE),
            title=title,
            status=InvestigationState.NEW,
            severity=severity,
            business_impact=business_impact,
            symptom=symptom,
            affected_scope=affected_scope,
            platform=platform,
            **kwargs,
        )
