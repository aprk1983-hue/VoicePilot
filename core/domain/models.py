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
    ID_PREFIX_FINDING,
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
    source_type: str | None = None
    raw_text: str | None = None
    source_artifact_id: str | None = None
    parser_finding_ids: list[str] = field(default_factory=list)
    supports_hypothesis_ids: list[str] = field(default_factory=list)
    contradicts_hypothesis_ids: list[str] = field(default_factory=list)

    @classmethod
    def create_cli_paste(
        cls,
        case_id: str,
        command: str,
        raw_text: str,
        *,
        collected_at: datetime | None = None,
    ) -> Evidence:
        """Factory for engineer-pasted CLI command output."""
        timestamp = collected_at or _utc_now()
        return cls(
            evidence_id=_new_id(ID_PREFIX_EVIDENCE),
            case_id=case_id,
            type="cli_output",
            title=f"CLI paste: {command}",
            source=EvidenceSource(
                origin="cli_paste",
                collector="engineer",
                command=command,
            ),
            collected_at=timestamp,
            quality=EvidenceQuality(
                completeness=1.0,
                freshness=1.0,
                reliability=1.0,
                parseability=1.0,
                overall=1.0,
            ),
            source_type="cli_paste",
            raw_text=raw_text,
        )


@dataclass(frozen=True)
class EvidenceRequest:
    """Prompt for the next required CLI evidence artifact."""

    case_id: str
    command: str
    sequence: int
    total: int


@dataclass(frozen=True)
class EvidenceSubmission:
    """Result of submitting pasted command output."""

    case_id: str
    command: str
    source_type: str
    raw_text: str
    collected_at: datetime
    evidence_id: str


@dataclass(frozen=True)
class AnalysisFinding:
    """Deterministic signal extracted from collected evidence."""

    finding_id: str
    case_id: str
    evidence_id: str
    command: str
    signal: str
    detected_at: datetime
    detail: str | None = None

    @classmethod
    def create(
        cls,
        case_id: str,
        evidence_id: str,
        command: str,
        signal: str,
        *,
        detail: str | None = None,
        detected_at: datetime | None = None,
    ) -> AnalysisFinding:
        """Factory for a v1 analysis finding."""
        return cls(
            finding_id=_new_id(ID_PREFIX_FINDING),
            case_id=case_id,
            evidence_id=evidence_id,
            command=command,
            signal=signal,
            detected_at=detected_at or _utc_now(),
            detail=detail,
        )


@dataclass
class Hypothesis:
    """Candidate or confirmed root cause explanation."""

    hypothesis_id: str
    case_id: str
    title: str
    status: HypothesisStatus = HypothesisStatus.CANDIDATE
    confidence: float = 0.0
    description: str | None = None
    category: str | None = None
    explanation: str | None = None
    next_best_action: str | None = None
    affected_device_ids: list[str] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    supporting_finding_ids: list[str] = field(default_factory=list)
    contradicting_finding_ids: list[str] = field(default_factory=list)
    rank: int | None = None
    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        case_id: str,
        title: str,
        confidence: float,
        supporting_finding_ids: list[str],
        *,
        explanation: str | None = None,
        next_best_action: str | None = None,
        contradicting_finding_ids: list[str] | None = None,
        rank: int | None = None,
        status: HypothesisStatus = HypothesisStatus.CANDIDATE,
        category: str | None = None,
    ) -> Hypothesis:
        """Factory for a ranked investigation hypothesis."""
        return cls(
            hypothesis_id=_new_id(ID_PREFIX_HYPOTHESIS),
            case_id=case_id,
            title=title,
            confidence=confidence,
            supporting_finding_ids=list(supporting_finding_ids),
            contradicting_finding_ids=list(contradicting_finding_ids or []),
            explanation=explanation,
            next_best_action=next_best_action,
            rank=rank,
            status=status,
            category=category,
        )


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
    required: bool = True
    answer_structured: JsonDict | None = None
    asked_at: datetime | None = None
    answered_at: datetime | None = None


@dataclass
class Recommendation:
    """Proposed next investigative action or likely root cause recommendation."""

    recommendation_id: str
    case_id: str
    action_type: str
    description: str
    rationale: str
    cost_level: str
    information_gain: float
    priority_rank: int
    status: RecommendationStatus = RecommendationStatus.RECOMMENDED
    confidence: float | None = None
    likely_root_cause: str | None = None
    evidence_summary: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    requires_engineer_approval: bool = False
    verification_steps: list[str] = field(default_factory=list)
    rollback_steps: list[str] = field(default_factory=list)
    hypothesis_id: str | None = None
    target_device_id: str | None = None
    command: str | None = None

    @classmethod
    def create(
        cls,
        case_id: str,
        action_type: str,
        description: str,
        rationale: str,
        *,
        confidence: float | None = None,
        likely_root_cause: str | None = None,
        evidence_summary: list[str] | None = None,
        recommended_actions: list[str] | None = None,
        verification_steps: list[str] | None = None,
        rollback_steps: list[str] | None = None,
        hypothesis_id: str | None = None,
        command: str | None = None,
        priority_rank: int = 1,
        cost_level: str = "low",
        information_gain: float = 0.0,
        requires_engineer_approval: bool = False,
    ) -> Recommendation:
        """Factory for an investigation recommendation."""
        return cls(
            recommendation_id=_new_id(ID_PREFIX_RECOMMENDATION),
            case_id=case_id,
            action_type=action_type,
            description=description,
            rationale=rationale,
            cost_level=cost_level,
            information_gain=information_gain,
            priority_rank=priority_rank,
            confidence=confidence,
            likely_root_cause=likely_root_cause,
            evidence_summary=list(evidence_summary or []),
            recommended_actions=list(recommended_actions or []),
            verification_steps=list(verification_steps or []),
            rollback_steps=list(rollback_steps or []),
            hypothesis_id=hypothesis_id,
            command=command,
            requires_engineer_approval=requires_engineer_approval,
        )


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
class InvestigationTurn:
    """A single turn in the runtime investigation loop presented to the engineer."""

    case_id: str
    state: InvestigationState
    prompt: str
    question_id: str | None
    expected_response_type: str
    available_options: list[str]
    required: bool
    context: JsonDict
    next_action_type: str


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
    analysis_findings: list[AnalysisFinding] = field(default_factory=list)
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
