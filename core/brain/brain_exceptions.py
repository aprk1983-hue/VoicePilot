"""Brain orchestration exceptions."""

from __future__ import annotations

from runtime.exceptions import VoicePilotRuntimeError


class BrainSessionNotFoundError(VoicePilotRuntimeError):
    """Raised when a Brain session ID is not registered."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Brain session not found: {session_id}")
        self.session_id = session_id


class DuplicateBrainSessionError(VoicePilotRuntimeError):
    """Raised when registering a Brain session with an existing ID."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Brain session already registered: {session_id}")
        self.session_id = session_id


class InvalidBrainStageError(VoicePilotRuntimeError):
    """Raised when a Brain operation is invalid for the current stage."""

    def __init__(self, session_id: str, message: str) -> None:
        super().__init__(f"Brain session {session_id}: {message}")
        self.session_id = session_id
