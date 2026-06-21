"""Investigation session domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.enums import InvestigationState
from shared.types import JsonDict


class InvestigationSessionStatus(str, Enum):
    """Lifecycle status for an interactive investigation session."""

    ACTIVE = "ACTIVE"
    AWAITING_INPUT = "AWAITING_INPUT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionActionType(str, Enum):
    """Deterministic orchestration step within a session."""

    INTAKE_QUESTION = "intake_question"
    DISCOVERY_PLANNING = "discovery_planning"
    COLLECT_EVIDENCE = "collect_evidence"
    RUN_ANALYSIS = "run_analysis"
    RUN_HYPOTHESIS = "run_hypothesis"
    RUN_CORRELATION = "run_correlation"
    QUALITY_EVALUATION = "quality_evaluation"
    COLLECT_DISCOVERY_EVIDENCE = "collect_discovery_evidence"
    RUN_RECOMMENDATION = "run_recommendation"
    RUN_VERIFICATION = "run_verification"
    RUN_CLOSURE = "run_closure"


@dataclass(frozen=True)
class SessionJourneyEntry:
    """Chronological record of a session orchestration step."""

    sequence: int
    timestamp: datetime
    action: SessionActionType
    case_state: InvestigationState
    summary: str


@dataclass(frozen=True)
class InvestigationSession:
    """Immutable interactive investigation session."""

    session_id: str
    case_id: str
    playbook_id: str
    status: InvestigationSessionStatus
    current_action: SessionActionType
    case_state: InvestigationState
    turn_number: int
    journey: tuple[SessionJourneyEntry, ...]
    started_at: datetime
    updated_at: datetime
    pending_question_id: str | None = None
    pending_evidence_command: str | None = None
    pending_prompt: str | None = None
    metadata: JsonDict | None = None


@dataclass(frozen=True)
class SessionContinueResult:
    """Result of advancing an investigation session."""

    session: InvestigationSession
    messages: tuple[str, ...]
    prompt: str | None = None
