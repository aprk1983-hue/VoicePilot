"""VoicePilot Brain — orchestration kernel for investigation engines."""

from brain.brain_bootstrap import default_brain_engine
from brain.brain_context import BrainContext
from brain.brain_engine import BrainEngine
from brain.brain_exceptions import (
    BrainSessionNotFoundError,
    DuplicateBrainSessionError,
    InvalidBrainStageError,
)
from brain.brain_models import (
    BrainAdvanceResult,
    BrainJourneyEntry,
    BrainReplayStep,
    BrainSession,
    BrainStage,
)
from brain.brain_registry import BrainRegistry
from brain.brain_report import (
    build_investigation_replay,
    format_brain_replay,
    format_brain_session_list,
    format_brain_status,
)

__all__ = [
    "BrainAdvanceResult",
    "BrainContext",
    "BrainEngine",
    "BrainJourneyEntry",
    "BrainRegistry",
    "BrainReplayStep",
    "BrainSession",
    "BrainSessionNotFoundError",
    "BrainStage",
    "DuplicateBrainSessionError",
    "InvalidBrainStageError",
    "build_investigation_replay",
    "default_brain_engine",
    "format_brain_replay",
    "format_brain_session_list",
    "format_brain_status",
]
