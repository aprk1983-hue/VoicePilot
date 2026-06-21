"""Brain orchestration domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BrainStage(str, Enum):
    """Deterministic orchestration stages for the VoicePilot Brain."""

    INITIALIZING = "INITIALIZING"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    PARSING = "PARSING"
    ANALYZING = "ANALYZING"
    CORRELATING = "CORRELATING"
    DISCOVERY_PLANNING = "DISCOVERY_PLANNING"
    QUALITY_EVALUATION = "QUALITY_EVALUATION"
    RECOMMENDING = "RECOMMENDING"
    VERIFYING = "VERIFYING"
    LEARNING = "LEARNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class BrainJourneyEntry:
    """Chronological Brain orchestration step."""

    sequence: int
    timestamp: datetime
    stage: BrainStage
    summary: str
    decision_log_id: str | None = None


@dataclass(frozen=True)
class BrainSession:
    """Immutable Brain orchestration session."""

    session_id: str
    case_id: str
    playbook: str
    current_stage: BrainStage
    started_at: datetime
    last_updated: datetime
    current_confidence: float | None
    current_quality_score: int | None
    completed: bool
    failed: bool
    decision_log_ids: tuple[str, ...]
    journey: tuple[BrainJourneyEntry, ...] = ()


@dataclass(frozen=True)
class BrainAdvanceResult:
    """Result of advancing a Brain session."""

    session: BrainSession
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class BrainReplayStep:
    """Single step in an investigation replay timeline."""

    timestamp: datetime
    label: str
    source: str
